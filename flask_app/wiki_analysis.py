# -*- coding: utf-8 -*-

import sys
reload(sys)
sys.setdefaultencoding("utf-8")

from flask import Flask
from flask import render_template

import json
import os
import psycopg2
import time

app = Flask(__name__)
conn = None

CACHE_TOP_VISITS = "./cache/topvisits.json"

@app.route("/collections/")
def collections():

    curs = conn.cursor()
    coll_sql = "select count(*), rev_collected from wiki_collections group by rev_collected order by rev_collected"
    curs.execute(coll_sql)
    res = curs.fetchall()
    coll_pcts = [{"label": "Uncollected: " + "{:,}".format(res[0][0]),
                  "value": res[0][0]},
                 {"label": "Collected: " + "{:,}".format(res[1][0]),
                  "value": res[1][0]}]

    if (int(time.time()) % 1800 == 0) or (not os.path.isfile(CACHE_TOP_VISITS)):
        print "Caching objects."
        cache_top_visits(50)
    tvisit_file = file(CACHE_TOP_VISITS, 'r')
    topvisits = json.load(tvisit_file)
    tvisit_file.close()

    next_n_sql = "SELECT wp.page_name FROM wiki_collections wc LEFT JOIN wiki_pages wp ON wc.page_id=wp.wpage_id WHERE rev_collected=FALSE ORDER BY coll_id ASC LIMIT %s"
    data = (25,)
    curs.execute(next_n_sql, data)
    results = curs.fetchall()

    next_n = []
    for res in results:
        next_n.append(res[0])

    top_users = "select count(*), wu.username from wiki_edits we left join wiki_usernames wu on wu.user_id=we.edit_user where we.edit_user!=12 group by wu.username order by count(*) desc limit %s"
    data = (100, )
    curs.execute(top_users, data)
    results = curs.fetchall()
    top_users_res = []
    for res in results:
        app_res = dict({"label": res[1], "value": res[0]})
        top_users_res.append(app_res)

    # user_count = "SELECT

    context = {
        "collected_pct": coll_pcts,
        "topvisits": topvisits,
        "next_n_collects": next_n,
        "topusers": top_users_res
    }

    return render_template('collection.html', context=context)


def cache_top_visits(numvisits):
    """
    Cache the top visits in a json file to serve up on the hour.
    :param numvisits:
    :return:
    """
    curs = conn.cursor()

    mvs_sql = "select count(*) as totals, wv.page_name from wiki_visits wv group by wv.page_name order by count(*) desc limit %s"
    data = (numvisits, )
    curs.execute(mvs_sql, data)
    res = curs.fetchall()
    cache_vals = []
    for item in res:
        app_val = dict({"value": item[0],
                        "label": item[1]})
        cache_vals.append(app_val)
    outfile = file(CACHE_TOP_VISITS, 'w')
    json.dump(cache_vals, outfile)
    outfile.close()


if __name__ == "__main__":
    conn_str = "dbname='jimmy1' user='jimmy1' " \
               "host='localhost' " \
               "port='5432' "
    conn = psycopg2.connect(conn_str)

    app.run(host='0.0.0.0', debug=True)
    # app.run()