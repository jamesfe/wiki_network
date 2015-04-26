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

