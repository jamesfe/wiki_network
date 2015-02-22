

import requests
import json
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

        tgt_sql = "SELECT coll_id FROM wiki_collections wc LEFT JOIN wiki_pages wp ON wc.page_id=wp.wpage_id WHERE rev_collected=FALSE"
        curs = self.conn.cursor()
        curs.execute(tgt_sql)
        res = curs.fetchall()
        for collect_id in res:
            self.collect_targets.append(collect_id)

        ## We keep this variable around as a kind of global so we know when the last API call we made
        ## was.  This is so we can only do one call per second.
        self.api_clock = time.time()
        self.api_reqrate = 1.1 # 1.1 seconds between each call

    def insert_seed(self):
        """
        Insert our seed article.  In this case, maybe "Albert Einstein" is a good choice.
        :return:
        """
        curs = self.conn()

        sql = "INSERT INTO wiki_pages (page_name) VALUES (%s)"
        data = "Albert Einstein"

        curs.execute(sql, data)

        sql = "SELECT wpage_id FROM wiki_pages WHERE page_name=%s"

        curs.execute(sql, data)
        res = curs.fetchone()

        sql = "INSERT INTO wiki_collections (page_id, rev_collected, seed_article, start_time) " \
              "VALUES (%s, FALSE, -1, NOW())"
        data = (res[0],)

        curs.execute(sql, data)

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
        pass

    def gather_revisions(self, page_id):
        """
        - Check the database to make sure the revisions for this page aren't already in it.
            - If there are, delete everything, we can grab new stuff.
        - Make a query to the Wikimedia API for revisions
        - Insert each revision into the wiki_edits table


        :param page_id:
        :return:
        """
        pass

    def gather_links(self, page_id):
        """
        Gather a number of links from each page.
        - Check to see if the page has already been inserted.
        - If not, insert each link.
        :param page_id:
        :return:
        """
        pass

    def add_username(self, username):
        """
        Add a username, if already inserted, just return its ID number.
        :param username: some string
        :return: user_id
        """
        pass

    def add_page(self, page_name):
        """
        Add a page's name to the database, if it's already there, just return an ID.
        :param page_name: some string
        :return:
        """
        pass