

import requests
import psycopg2
import time
import re

REQYEARS = ('2014', '2015')

class WikiCollector:
    """
    This is a collector for wikipedia information.  We are collecting revisions, the size of the article at the end
    of the revision, and the author of the revision as well as ancillary data (timestamp, etc.)

    - We instantiate the class.
        - It connects to the database
        - It figures out which pages it needs to get
        - It inserts the revisions for each article into the database
    """
    def __init__(self):
        """
        Initiator - make a database connection, figure out where we are, etc.
        :return:
        """
        conn_str = "dbname='jimmy1' user='jimmy1' " \
                   "host='localhost' " \
                   "port='5432' "
        self.conn = psycopg2.connect(conn_str)
        self.collect_targets = list()

        curs = self.conn.cursor()

        sql = "SELECT COUNT(*) FROM wiki_pages"
        curs.execute(sql)
        res = curs.fetchall()
        print "Current results in database: ", res
        if res[0][0] == 0:
            print "Inserting seed."
            self.insert_seed()

        ## We keep this variable around as a kind of global so we know when the last API call we made
        ## was.  This is so we can only do one call per second.
        self.api_clock = time.time()
        self.api_reqrate = 1.1  # 1.1 seconds between each call

        self.badnames = re.compile('^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$')

    def insert_seed(self):
        """
        Insert our seed article.  In this case, maybe "Albert Einstein" is a good choice.
        :return:
        """
        curs = self.conn.cursor()

        page_id = self.add_page("Aage Bohr", -1)

        sql = "INSERT INTO wiki_collections (page_id, rev_collected, seed_article, start_time) " \
              "VALUES (%s, FALSE, -1, NOW())"
        data = (page_id,)

        curs.execute(sql, data)

    def perform_collections(self):
        """
        Main thread - actually do the collections.
        :return:
        """
        print "Performing collections"
        curs = self.conn.cursor()
        sql = "SELECT page_id FROM wiki_collections WHERE rev_collected = FALSE ORDER BY coll_id ASC LIMIT 1"
        ## Watch out, we use the above sql statement later again (in a loop!)
        curs.execute(sql)
        res = curs.fetchone()
        while res is not None:
            print time.asctime(), "Collecting result: ", res[0], self.get_page_name(res[0])
            self.collect_page(res[0])
            curs.execute(sql)
            res = curs.fetchone()

    def collect_page(self, page_id):
        """
        Responsibilities:
            Given the page on the list, check that it's not already in the database as collected.
            If it is, return 'whatever'.
            If not, it's already in the database, so do this:
                - Request a list of all the revisions on that page.
                - Insert each revision into the database.
                - Reuest a list of each page referenced from the seed.
                - Insert each of those pages into the wiki_pages table
                - Insert each un-collected page into the wiki-collections table.
        :return:
        """
        curs = self.conn.cursor()
        links = self.gather_links(page_id)
        for link in links:
            self.add_page(link['title'], page_id)

        page_revisions = self.gather_revisions(page_id)
        entries = 0
        for revision in page_revisions:
            sql = "INSERT INTO wiki_edits (edit_time, edit_user, edit_page, pagesize," \
                  "pagedelta, revid, parentrev) VALUES (%s, %s, %s, %s, -1, %s, %s)"
            timestamp = revision['timestamp'] ## apparently this is fine with postgresql
            if timestamp[0:4] in REQYEARS:
                try:
                    user_id = self.add_username(revision['user'])
                except KeyError:
                    print "Key error on ", revision
                    user_id = self.add_username("Auto: Program error, username")
                data = (timestamp, user_id, page_id, revision['size'], revision['revid'],
                        revision['parentid'])
                curs.execute(sql, data)
                entries += 1
        print "Entered revisions: ", entries
        sql = "UPDATE wiki_collections SET rev_collected=TRUE WHERE page_id=%s "
        data = (page_id, )
        curs.execute(sql, data)
        self.conn.commit()

    def gather_revisions(self, page_id):
        """
        - Check the database to make sure the revisions for this page aren't already in it.
            - If there are, delete everything, we can grab new stuff.
        - Make a query to the Wikimedia API for revisions
        - Insert each revision into the wiki_edits table
        :param page_id:
        :return:
        =timestamp|user|comment|size|ids&format=json&rvlimit=500&continue=
        """
        page_name = self.get_page_name(page_id)
        payload = dict({
            "action": "query",
            "prop": "revisions",
            "titles": page_name,
            "rvprop": "timestamp|user|size|ids",
            "format": "json",
            "rvlimit": 500,
            "continue": ""
        })

        return self.wiki_rev_query(payload)

    def wiki_rev_query(self, params):
        """
        Query and return all the revisions for this page.
        :param params:
        :return:
        """
        headers = dict({
            "User-Agent": "Wiki_Network_Collections 1.0 (no url; james.ferrara@gmail.com) "
                          "Using Python Requests/v.2.5.3"
        })
        last_continue = ''
        rv_continue = None
        query_res = []
        while True:
            # Modify it with the values returned in the 'continue' section of the last result.
            params['continue'] = last_continue
            if rv_continue is not None:
                params['rvcontinue'] = rv_continue
            # Call API
            self.api_checktime()
            result = requests.get('http://en.wikipedia.org/w/api.php', params=params, headers=headers)
            result = result.json()

            if 'error' in result:
                raise ValueError(result['error'])
            if 'warnings' in result:
                print(result['warnings'])
            if 'query' in result:
                try:
                    query_res.extend(result['query']['pages'].values()[0]['revisions'])
                    lastobj = result['query']['pages'].values()[0]['revisions'][-1]
                    if lastobj['timestamp'][0:4] not in REQYEARS:
                        break
                except KeyError:
                    break
            if 'continue' not in result:
                break
            rv_continue = result['continue']['rvcontinue']
            last_continue = result['continue']['continue']
        return query_res

    def get_page_name(self, page_id):
        """
        from a page_id, return a page name
        :param page_id:
        :return:
        """
        curs = self.conn.cursor()
        sql = "SELECT page_name FROM wiki_pages WHERE wpage_id=%s LIMIT 1"
        data = (page_id, )
        curs.execute(sql, data)
        res = curs.fetchone()
        if res is None:
            return -1
        return res[0]

    def gather_links(self, page_id):
        """
        Gather a number of links from each page.
        - Check to see if the page has already been inserted.
        - If not, insert each link.
        :param page_id:
        :return:
        """
        # http://en.wikipedia.org/w/api.php?action=query&titles=[[page_title]]&prop=links&format=json&pllimit=500&continue=
        page_name = self.get_page_name(page_id)

        headers = dict({
            "User-Agent": "Wiki_Network_Collections 1.0 (no url; james.ferrara@gmail.com) "
                          "Using Python Requests/v.2.5.3"
        })

        params = dict({
            "action": "query",
            "titles": page_name,
            "prop": "links",
            "format": "json",
            "pllimit": 500,
            "continue": ""
        })

        last_continue = ''
        pl_continue = None
        query_res = []
        while True:
            # Modify it with the values returned in the 'continue' section of the last result.
            params['continue'] = last_continue
            if pl_continue is not None:
                params['plcontinue'] = pl_continue
            # Call API
            self.api_checktime()
            result = requests.get('http://en.wikipedia.org/w/api.php', params=params, headers=headers)
            result = result.json()

            if 'error' in result:
                raise ValueError(result['error'])
            if 'warnings' in result:
                print("Gather Pages: ", result['warnings'])
            if 'query' in result:
                try:
                    query_res.extend(result['query']['pages'].values()[0]['links'])
                except KeyError:
                    break
            if 'continue' not in result:
                break
            pl_continue = result['continue']['plcontinue']
            last_continue = result['continue']['continue']
        return query_res

    def api_checktime(self):
        """
        Check the time, wait if necessary, and log a new api request.
        :return:
        """
        if time.time() < (self.api_clock + self.api_reqrate):
            time.sleep(self.api_reqrate)
        self.api_clock = time.time()

    def add_username(self, username):
        """
        Add a username, if already inserted, just return its ID number.
        :param username: some string
        :return: user_id
        """
        username = username.strip()
        if self.badnames.match(username) is not None:
            username = "AUTO: anonymous ip address"

        curs = self.conn.cursor()
        sql = "SELECT user_id FROM wiki_usernames WHERE username=%s"
        data = (username, )
        curs.execute(sql, data)
        res = curs.fetchone()
        if res is not None and len(res) > 0:
            return res[0]
        else:
            sql = "INSERT INTO wiki_usernames (username) VALUES (%s) RETURNING user_id"
            # Reusing data here.  Bad code smell?
            curs.execute(sql, data)
            res = curs.fetchone()
            self.conn.commit()
            return res[0]

    def add_page(self, page_name, seed_article):
        """
        Add a page's name to the database, if it's already there, just return an ID.
        :param page_name: some string
        :return:
        """
        curs = self.conn.cursor()

        # Log the visit, then see if the page is already in existance.
        visit_sql = "INSERT INTO wiki_visits (page_name, visit_time) VALUES (%s, NOW())"
        visit_data = (page_name, )
        curs.execute(visit_sql, visit_data)
        self.conn.commit()

        sql = "SELECT wpage_id FROM wiki_pages WHERE page_name=%s"
        data = (page_name, )
        curs.execute(sql, data)
        res = curs.fetchone()
        if res is not None:
            return res[0]
        else:
            sql = "INSERT INTO wiki_pages (page_name) VALUES (%s) RETURNING wpage_id"
            # Reusing data here.  Bad code smell?
            curs.execute(sql, data)
            res = curs.fetchone()

            coll_val = False

            ignorevals = ["Template talk:", "File:", "Talk:", "Template:", "Help:", "Wikipedia:", "Portal:", "Category:", "Book:", "User:", "User talk:"]
            for val in ignorevals:
                if page_name.find(val) == 0:
                    coll_val = True

            collect_sql = "INSERT INTO wiki_collections (page_id, rev_collected, seed_article, start_time) " \
                          "VALUES (%s, %s, %s, NOW())"
            coll_data = (res[0], coll_val, seed_article)
            curs.execute(collect_sql, coll_data)

            self.conn.commit()
            return res[0]


if __name__ == "__main__":
    wkcoll = WikiCollector()
    wkcoll.perform_collections()