from py2neo import Graph
from py2neo import Node, Relationship

n4jconn = None


def connect():
    """
    Globally connect.
    :return:
    """
    global n4jconn
    n4jconn = Graph()
    return n4jconn

if __name__ == "__main__":
    if n4jconn is None:
        connect()

    n4jconn.delete_all()
    p1 = Node("Person", name="Mike")
    p2 = Node("Person", name="John")
    n4jconn.create(p1, p2)




