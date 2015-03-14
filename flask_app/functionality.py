"""
Analysis functions that can be separated from Flask
"""

import psycopg2

conn = None


def cache_build_ratios():
    """
    Cache the ratio of collected to uncollected items
    - pick an item from collections
    - identify the number of pages collected and uncollected at that point (by timestamp)
    - identify number of visits beyond that point
    :return:
    """
    curs = conn.cursor()
    sql = "SELECT page_id, coll_id, start_time FROM wiki_collections WHERE rev_collected=TRUE and coll_id < " \
          "(SELECT coll_id FROM wiki_collections WHERE rev_collected=FALSE ORDER BY coll_id ASC LIMIT 1) " \
          "order by coll_id ASC LIMIT 100"

    curs.execute(sql)
    results = curs.fetchall()
    for res in results:
        print res
        pass


def get_scatterplot_parent_seeds():
    """
    holding function for this SQL query:
    select count(*),seed_article from wiki_collections group by seed_article order by seed_article ASC limit 10;

    :return:
    """
    pass

if __name__ == "__main__":
    conn_str = "dbname='jimmy1' user='jimmy1' " \
               "host='localhost' " \
               "port='5432' "
    conn = psycopg2.connect(conn_str)

    cache_build_ratios()