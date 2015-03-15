"""
Analysis functions that can be separated from Flask
"""

import psycopg2
import time

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
    sql = "select page_id, start_time from wiki_collections WHERE rev_collected=TRUE order by coll_id asc "

    curs.execute(sql)
    results = curs.fetchall()
    coll_arr = list()
    article_count = 0
    for res in results:
        app_dict = dict({"page_id": res[0], "start_time": res[1]})
        coll_arr.append(app_dict)
        ratio_sql = "select count(*) from wiki_collections where seed_article<=%s"
        ratio_data = (app_dict['page_id'],)
        curs.execute(ratio_sql, ratio_data)
        ratio_res = curs.fetchone()

        log_ratio_sql = "INSERT INTO wiki_edits_ratio (num_collected, num_uncollected, curr_page_id) VALUES (%s, %s, %s)"
        log_ratio_data = (article_count, ratio_res[0], app_dict['page_id'])
        curs.execute(log_ratio_sql, log_ratio_data)

        article_count += 1

    conn.commit()
    print "Done building list and updating edit counts"
    # For each item in the collection array, we select all the visits that happened *before*
    # the timestamp of the item ahead of it.
    for index in range(0, len(coll_arr) - 1):
        print time.time(), index
        visit_sql = "SELECT count(*) from wiki_visits WHERE visit_time < %s"
        visit_data = (coll_arr[index + 1]['start_time'], )
        curs.execute(visit_sql, visit_data)
        visited_res = curs.fetchone()

        log_visit_sql = "UPDATE wiki_edits_ratio SET num_visited = %s WHERE curr_page_id = %s"
        log_visit_data = (visited_res[0], coll_arr[index]['page_id'])
        curs.execute(log_visit_sql, log_visit_data)

    conn.commit()
    print "done"



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