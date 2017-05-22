# -*- coding: utf-8 -*-
import json
import random
import re
from datetime import datetime

def login():
    username = request.vars['username']
    if not username:
        # First loading the page
        return dict()
    else:
        contribution_points = 0
        username = username.lower()
        # Form submitted
        user = db(db.user_info.name == username).select().first()
        if not user:
            # User does not exist. Insert
            user_id = db.user_info.insert(
                name = username,
                date_added = datetime.now(),
                contribution_points = 0
            )
        else:
            # user exists
            user_id = user.id
            contribution_points = user.contribution_points
        # Set session
        session.user_id = user_id
        session.user_name = username
        session.contribution_points = contribution_points
        # Redirect to page
        redirect(URL(request.application, 'default', 'page?page_num=1'))

def page():
    __check_username()
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
    return dict(page_num=page_num, discussions=discussions, concepts=concepts, user_name=session.user_name, contribution_points=session.contribution_points)

def submit_new_discussion():
    # get data
    title = request.vars.title
    description = request.vars.description
    kind = request.vars.kind
    date_added = datetime.now()
    page_num = request.vars.page_num
    added_by = session.user_id
    # Deal with hashtags
    concepts = re.findall(r"#(\w+)", description) # From http://stackoverflow.com/questions/2527892/parsing-a-tweet-to-extract-hashtags-into-an-array-in-python
    ids = []
    for c in concepts:
        ids.append(__insert_concept(c, page_num))
    # Validate TODO fancier validation, also at client side
    if not title or not description or not kind:
        response.status = 500
        return 'All fields are mandatory!'
    # Insert discussion
    discussion_id = db.discussion.insert(
        title = title,
        kind = kind,
        description = description,
        page_num = page_num,
        added_by = added_by,
        date_added = date_added
    )
    # Connect concept and discussion
    for i in ids:
        db.concept_discussion.insert(
            concept = i,
            discussion = discussion_id
        )
    return json.dumps(discussion_id)

def get_discussions_for_tag():
    tag = request.vars.tag
    discussions = db((db.concept_discussion.discussion == db.discussion.id) &
        (db.concept_discussion.concept == db.concept.id) &
        (db.discussion.added_by == db.user_info.id) &
        (db.concept.name == tag)).select(groupby=db.discussion.id, orderby=db.discussion.page_num)
    clean_discussions = [dict(
            id=d.discussion.id,
            title=d.discussion.title,
            added_by=d.user_info.name,
            date_added=str(d.discussion.date_added),
            page_num=d.discussion.page_num)
        for d in discussions]
    return json.dumps(clean_discussions)

def discussion():
    __check_username()
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
    # Retrieve task types for discussion messages
    tasks = db(db.task_definition.task_type == 'discussion_reply').select()
    # Retrieve completed tasks by the user
    completed_tasks = db((db.task.task_definition == db.task_definition.id) &
        (db.task.completed_by == current_user_id) &
        (db.task_definition.task_type == 'discussion_reply')).select(db.task.associated_to, db.task.task_definition)
    # turn into a convenient format for the view
    ct_dict = dict()
    for ct in completed_tasks:
        if ct.associated_to not in ct_dict.keys():
            ct_dict[ct.associated_to] = []
        ct_dict[ct.associated_to].append(ct.task_definition)
    print(ct_dict)
    # return
    return dict(
        discussion_id=id, 
        user_name='Test user', 
        current_user_id=current_user_id, 
        discussion=discussion, 
        discussion_messages=discussion_messages, 
        tasks=tasks,
        contribution_points=session.contribution_points, 
        page_num=discussion.page_num,
        completed_tasks=ct_dict)

def submit_discussion_reply():
    # get vars
    message = request.vars.message
    discussion_id = request.vars.discussion_id
    date_added = datetime.now()
    user_id = session.user_id
    # Insert in DB
    reply_id = db.discussion_message.insert(
        discussion = discussion_id,
        message_content = message,
        date_added = date_added,
        added_by = user_id
    )
    return json.dumps(dict(
        id = reply_id,
        message = message,
        timestamp = str(date_added),
        user_name = reply_id # TODO Should fetch username
    ))

def submit_task():
    associated_to = request.vars.contentId
    task_definition = request.vars.id
    user_input = request.vars['userInput']
    completed_by = session.user_id
    points = int(request.vars.points)
    # insert task completion
    db.task.insert(
        associated_to=associated_to,
        task_definition=task_definition,
        user_input=user_input,
        completed_by=completed_by)
    # update points for user
    user = db(db.user_info.id == completed_by).select().first()
    user.contribution_points = user.contribution_points + points
    user.update_record()
    # Update in session
    session.contribution_points = user.contribution_points
    # Check if threshold is exceeded
    definition = db(db.task_definition.id == task_definition).select().first()
    count = db((db.task.task_definition == task_definition) &
        (db.task.associated_to == associated_to)).count()
    print('Count >= definition.threshold: %d >= %d' % (count, definition.threshold))
    if count >= definition.threshold:
        # If the addition of this action passes the threshold, add badge to item
        item = db(db.discussion_message.id == associated_to).select().first()
        badges = set()
        if item.badges:
            badges = set(item.badges)
        badges.add(definition.id)
        item.badges = list(badges)
        item.update_record()
    return user.contribution_points

def get_badge_data():
    reply_id = request.vars.reply_id
    task_definition_id = request.vars.task_id
    answers = db((db.task.associated_to == reply_id) &
        (db.task.task_definition == task_definition_id)).select(db.task.user_input)
    results = []
    for a in answers:
        results += a.user_input
    return json.dumps(results)
        


def __check_username():
    if session.user_id == None:
        redirect(URL(request.application, 'default', 'login'))

def __insert_concept(name, page):
    concept = db(db.concept.name == name).select().first()
    if not concept:
        # This is a new concept
        id = db.concept.insert(name=name,related_pages=[page], color=__random_color())
        return id
    else:
        print(concept.related_pages)
        # Concept exists. Simply add a reference to this page
        if not long(page) in concept.related_pages:
            concept.related_pages.append(page)
            concept.update_record()
        return concept.id

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