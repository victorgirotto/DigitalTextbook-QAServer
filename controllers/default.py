# -*- coding: utf-8 -*-
import random

def page():
    page_num = request.vars.page_num
    # Validating params
    if not page_num:
        # Mandatory param was not found
        response.status = 500
        return 'You must supply a page_num param'

    # Retrieve discussions for page page_num
    discussions = db(
        (db.discussion.page_num == page_num) &
        (db.discussion.added_by == db.user_info.id)).select(groupby=db.discussion.id)
    # Retrieve concepts that exist in page
    concepts = db(db.concept.related_pages.contains(page_num)).select()
    # Return values
    return dict(page_num=page_num, discussions=discussions, concepts=concepts)

def add_concepts():
    concepts = ['another','tree','extinction','bird','observer']
    for c in concepts:
        __insert_concept(c,1)

def __insert_concept(name, page):
    db.concept.insert(name=name,related_pages=[page], color=__random_color())

def __random_color():
    colors = [
        "#F49AC2",
        "#CB99C9",
        "#C23B22",
        "#FFD1DC",
        "#DEA5A4",
        "#AEC6CF",
        "#77DD77",
        "#CFCFC4",
        "#B39EB5",
        "#FFB347",
        "#B19CD9",
        "#FF6961",
        "#03C03C",
        "#FDFD96",
        "#836953",
        "#779ECB",
        "#966FD6"]
    return random.choice(colors)