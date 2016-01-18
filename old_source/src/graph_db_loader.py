from py2neo import Graph
from py2neo import Node, Relationship
import psycopg2
import time

n4jconn = None
pgconn = None


def connect():
    """
    Globally connect.
    :return:
    """
    global n4jconn
    n4jconn = Graph()
    return n4jconn


def pg_get_nodes(num_nodes):
    """
    Get some wikipedia articles from Postgres
    :param num_nodes:
    :return:
    """
    curs = conn.cursor()
    cols = ['rev_collected', 'page_id', 'seed_article', 'start_time', 'page_name']
    sql = "select " + ', '.join(cols) + " " \
          "from wiki_collections wc LEFT JOIN wiki_pages wp ON wc.page_id=wp.wpage_id ORDER BY page_id ASC LIMIT %s"
    data = (num_nodes, )
    curs.execute(sql, data)
    results = curs.fetchall()

    ret_vals = []
    for res in results:
        newdict = dict()
        for index, col in enumerate(cols):
            newdict[col] = res[index]
        ret_vals.append(newdict)
    return ret_vals


if __name__ == "__main__":
    if n4jconn is None:
        connect()

    conn_str = "dbname='jimmy1' user='jimmy1' " \
               "host='localhost' " \
               "port='5432' "
    conn = psycopg2.connect(conn_str)

    n4jconn.delete_all()
    # p1 = Node("Person", name="Mike")
    # p2 = Node("Person", name="John")
    # n4jconn.create(p1, p2)

    print time.asctime(), "Entering nodes."
    new_nodes = pg_get_nodes(1000)
    for item in new_nodes:
        it2 = dict()
        nnode = Node.cast("Article", item)
        n4jconn.create(nnode)

    print time.time(), "Beginning to enter relationships."

    numrelationships = 0
    numerrors = 0
    for item in new_nodes:
        from_node = n4jconn.find_one("Article", 'page_id', item['seed_article'])
        to_node = n4jconn.find_one("Article", 'page_id', item['page_id'])
        rel = Relationship(from_node, "collected to", to_node)
        try:
            n4jconn.create(rel)
            numrelationships += 1
        except AttributeError:
            numerrors += 1
            pass
    print time.time(), "Relationships entered: ", numrelationships,


