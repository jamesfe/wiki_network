

import requests
import psycopg2
import time


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

    def insert_seed(self):
        """
        Insert our seed article.  In this case, maybe "Albert Einstein" is a good choice.
        :return:
        """
        curs = self.conn.cursor()

        sql = "INSERT INTO wiki_pages (page_name) VALUES (%s)"
        data = ("Albert Einstein", )

        curs.execute(sql, data)

        sql = "SELECT wpage_id FROM wiki_pages WHERE page_name=%s"

        curs.execute(sql, data)
        res = curs.fetchone()

        sql = "INSERT INTO wiki_collections (page_id, rev_collected, seed_article, start_time) " \
              "VALUES (%s, FALSE, -1, NOW())"
        data = (res[0],)

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
            print "Collecting result: ", res
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
        links = self.gather_links(page_id)
        for key in links['query']['pages']:
            for link in links['query']['pages'][key]['links']:
                self.add_page(link['title'], page_id)

        page_revisions = self.gather_revisions(page_id)
        ## TODO: Insert each revision into the database.

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
            "rvprop": "timestamp|user|comment|size|ids",
            "format": "json",
            "rvlimit": 500,
            "continue": ""
        })

        revisions = []

        revs = self.wiki_query(payload)
        print revs
        for r in revs:
            for key in r['query']['pages']:
                for rev in r['query']['pages'][key]['revisions']:
                    revisions.append(rev)
        return revisions

    def wiki_query(self, params):
        ## TODO: Ensure we are gathering all revisions.  Check against DB.
        headers = dict({
            "User-Agent": "Wiki_Network_Collections 1.0 (no url; james.ferrara@gmail.com) "
                          "Using Python Requests/v.2.5.3"
        })
        last_continue = ''
        query_res = []
        while True:
            # Modify it with the values returned in the 'continue' section of the last result.
            params['continue'] = last_continue
            # Call API
            self.api_checktime()
            result = requests.get('http://en.wikipedia.org/w/api.php', params=params, headers=headers).json()
            # print params, result
            if 'error' in result:
                raise ValueError(result['error'])
            if 'warnings' in result:
                print(result['warnings'])
            if 'query' in result:
                query_res.append(result)
            if 'continue' not in result:
                # print "no continue, breaking"
                break
            last_continue = result['continue']
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

        payload = dict({
            "action": "query",
            "titles": page_name,
            "prop": "links",
            "format": "json",
            "pllimit": 500,
            "continue": ""
        })
        headers = dict({
            "User-Agent": "Wiki_Network_Collections 1.0 (no url; james.ferrara@gmail.com) "
                          "Using Python Requests/v.2.5.3"
        })

        self.api_checktime()
        api_req = requests.get("http://en.wikipedia.org/w/api.php",
                               params=payload,
                               headers=headers)

        try:
            api_json = api_req.json()
            # There's a chance that there are more than 500 results, but I think
            # that other pages will eventually collect those.
            # TODO: Fix it.
            return api_json
        except ValueError:
            return -1

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
        curs = self.conn.cursor()
        sql = "SELECT user_id FROM wiki_usernames WHERE username=%s"
        data = (username, )
        curs.execute(sql, data)
        res = curs.fetchone()
        if len(res) > 0:
            return res[0]
        else:
            sql = "INSERT INTO wiki_usernames (username) VALUE (%s) RETURNING user_id"
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

            collect_sql = "INSERT INTO wiki_collections (page_id, rev_collected, seed_article, start_time) " \
                          "VALUES (%s, FALSE, %s, NOW())"
            coll_data = (res[0], seed_article)
            curs.execute(collect_sql, coll_data)

            self.conn.commit()
            return res[0]


if __name__ == "__main__":
    wkcoll = WikiCollector()
    wkcoll.gather_revisions(1)
    # wkcoll.perform_collections()