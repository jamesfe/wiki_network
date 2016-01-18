# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import, unicode_literals, division

import unittest
import psycopg2



class TestPageDeltaFramework(unittest.TestCase):

    def setUp(self):
        """
        Set up a connection to the database
        (I suppose that makes this more of an integration framework)
        :return:
        """
        conn_str = "dbname='jimmy1' user='jimmy1' " \
                   "host='localhost' " \
                   "port='5432' "
        self.conn = psycopg2.connect(conn_str)

    def test_prev_edit_proper(self, before_edit, after_edit):
        """
        Are these two edits before & after each other?
        :param before_edit:
        :param after_edit:
        :return:
        """
        query = "SELECT wedit_id FROM wiki_edits WHERE edit_time < (SELECT edit_time FROM wiki_edits WHERE wedit_id=%s) LIMIT 1 ORDER BY edit_time DESC"
        data = (before_edit, )
        curs = self.conn.cursor()
        curs.execute(query, data)
        res = curs.fetchone()

        if res is not None:
            self.assertEqual(res[0], after_edit)

    def test_delta_size(self, before_edit, expected_editsize):
        """

        :param before_edit:
        :param expected_editsize:
        :return:
        """
        pass


if __name__ == '__main__':
    unittest.main()
