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

    context = {
        "collected_pct": coll_pcts,
        "topvisits": topvisits
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

    app.run(host='0.0.0.0')
    # app.run()