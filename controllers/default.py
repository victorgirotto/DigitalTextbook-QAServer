# -*- coding: utf-8 -*-
import json
import random
from datetime import datetime

session.user_id = 1

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
    return dict(page_num=page_num, discussions=discussions, concepts=concepts, user_name='Test user', contribution_points=21)

def submit_new_discussion():
    # get data
    title = request.vars.title
    description = request.vars.description
    date_added = datetime.now()
    page_num = request.vars.page_num
    added_by = 1 # TODO Figure out how we're handling users
    # Validate TODO fancier validation, also at client side
    if not title or not description:
        response.status = 500
        return 'All fields are mandatory!'
    # Insert discussion
    discussion_id = db.discussion.insert(
        title = title,
        description = description,
        page_num = page_num,
        added_by = added_by,
        date_added = date_added
    )
    return json.dumps(discussion_id)

def discussion():
    id = request.vars.id
    # Validating params
    if not id:
        # Mandatory param was not found
        response.status = 500
        return 'You must supply a id param'
    # Retrieve discussion messages
    discussion_messages = db(
        (db.discussion_message.discussion == id) & 
        (db.discussion_message.added_by == db.user_info.id)).select()
    # Retrieve discussion
    discussion = db((db.discussion.id == id)).select().first()
    current_user_id = session.user_id
    # TODO retrieve messages for discussion, return correct page_num
    return dict(user_name='Test user', current_user_id=current_user_id, discussion=discussion, discussion_messages=discussion_messages, contribution_points=21, page_num=1)

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