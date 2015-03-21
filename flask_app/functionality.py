"""
Analysis functions that can be separated from Flask
"""

import psycopg2
import time

conn = None


def build_revisit_timeline(page_id, start_time, end_time, time_step):
    """
    Given a start time, end time, and increments, find the average number of revisits for a page.
    How do we do this?
    - Select all the visits and their times
    - Bucket the visits based on the time steps
    :param page_id:
    :param start_time:
    :param end_time:
    :param time_step:
    :return:
    """
    curs = conn.cursor()
    ## TODO - build a histogram here.


def cache_build_ratios():
    """
    Cache the ratio of collected to uncollected items
    - pick an item from collections
    - identify the number of pages collected and uncollected at that point (by timestamp)
    - identify number of visits beyond that point
    TODO: Should this be a part of the main collections scripts?
    :return:
    """
    curs = conn.cursor()
    sql = "select page_id, start_time from wiki_collections WHERE rev_collected=TRUE order by coll_id asc "

    curs.execute(sql)
    results = curs.fetchall()
    coll_arr = list()
    article_count = 0
    insert_statements = []
    current_seed = -1

    print "Starting count metrics: ", time.asctime()
    for res in results:
        app_dict = dict({"page_id": res[0], "start_time": res[1]})
        coll_arr.append(app_dict)
        ratio_sql = "select count(*) from wiki_collections where seed_article<=%s and seed_article>=%s"
        ratio_data = (app_dict['page_id'], current_seed)
        curs.execute(ratio_sql, ratio_data)
        ratio_res = curs.fetchone()
        current_seed = app_dict['page_id']

        log_ratio_sql = "INSERT INTO wiki_edits_ratio (num_collected, num_uncollected, curr_page_id) VALUES (%s, %s, %s)"
        log_ratio_data = (article_count, ratio_res[0], app_dict['page_id'])
        # curs.execute(log_ratio_sql, log_ratio_data)
        insert_statements.append([log_ratio_sql, log_ratio_data])
        article_count += 1
    print "Finishing count metrics: ", time.asctime()

    print "Inserting rows...",
    for sql, data in insert_statements:
        curs.execute(sql, data)
    conn.commit()
    print "done"

    conn.commit()
    print "Done building list and updating edit counts"

    db_updates = list()
    # For each item in the collection array, we select all the visits that happened *before*
    # the timestamp of the item ahead of it.
    print "Starting visit metrics: ", time.asctime()
    for index in range(0, len(coll_arr) - 1):
        visit_sql = "SELECT count(*) from wiki_visits WHERE visit_time < %s"
        # TODO:  Perhaps I should change this SQL column to be numeric?  (Unix timestamp?)
        visit_data = (coll_arr[index + 1]['start_time'], )
        curs.execute(visit_sql, visit_data)
        visited_res = curs.fetchone()

        log_visit_sql = "UPDATE wiki_edits_ratio SET num_visited = %s WHERE curr_page_id = %s"
        log_visit_data = (visited_res[0], coll_arr[index]['page_id'])
        db_updates.append([log_visit_sql, log_visit_data])
    print "Finishing visit metrics: ", time.asctime()

    print "Updating database...",
    for sql, data in db_updates:
        curs.execute(sql, data)
    conn.commit()
    print "done."

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