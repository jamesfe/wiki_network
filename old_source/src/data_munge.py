"""
This file contains a few functions for munging the data and doing some prep.

Some tasks:
- Content deltas:
    - For each article, from the first edit forward, calculate the page deltas
        of each edit.
    - For each user, calculate some statistics and stash them away (probably better to do this in ES but alas):
        - Average size of edit
        - Variance of edit
        - Frequency of edit
        - Number of articles edited
        -
"""


def find_prev_edit_info(wiki_edit_id=None):
    """
    returns the previous edit's id & page size
    :param wiki_edit:
    :return:
    """

    return dict({"id": -1, "pagesize": -1})


def set_new_pagedeelta(wiki_edit_id=None):
    """
    In SQL, set the requested page's size and return nothing
    :param wiki_edit_id:
    :return: Nothing
    """

    # do some sql here
    pass


def get_pagesize(wiki_edit_id=None):
    """
    Return the pagesize of the current ID
    :param wiki_edit_id:
    :return: int
    """
    return -1


def fix_deltas(article_id):
    """
    Set all the deltas in an entire article
    EFFICIENCY: Get a whole row of things sorted properly and run them through the pipeline
    :param article_id:
    :return:
    """

    # do some function calls here
    pass