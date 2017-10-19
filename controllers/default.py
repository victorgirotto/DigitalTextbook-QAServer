# -*- coding: utf-8 -*-
import json
import random
import re
import operator
from datetime import datetime
from gluon.contrib.websocket_messaging import websocket_send
from collections import defaultdict

ADD_DISCUSSION_POINTS = 15
CLASSIFICATION_THRESHOLD = 3

EVENTS = dict(
    new_discussion="discussion",
    new_comment="comment"
)

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
        # (db.discussion.page_num == page_num) &
        (db.discussion.added_by == db.user_info.id)).select(groupby=db.discussion.id, orderby=db.discussion.page_num)
    # Retrieve concepts that exist in page
    concepts = db(db.concept.related_pages.contains(page_num)).select()
    # Retrieve user upvotes
    upvotes = db(db.upvote.user_info == session.user_id).select(db.upvote.discussion)
    upvotes = [d.discussion for d in upvotes]
    # Return values
    return dict(
        page_num=page_num, 
        discussions=discussions, 
        concepts=concepts, 
        user_name=session.user_name, 
        user_upvotes = upvotes,
        contribution_points=session.contribution_points)

def toggle_upvote():
    user_id = session.user_id
    discussion_id = request.vars.discussion
    # get discussion
    discussion = db(db.discussion.id == discussion_id).select().first()
    # check if already exists
    upvotes = db((db.upvote.discussion == discussion_id) & (db.upvote.user_info == user_id)).select()
    upvote = upvotes.first()
    exists = True if len(upvotes) > 0 else False
    if exists:
        # User is removing the upvote
        db((db.upvote.discussion == discussion_id) & (db.upvote.user_info == user_id)).delete()
        discussion.upvotes = discussion.upvotes - 1
        discussion.update_record()
    else:
        # User is upvoting
        db.upvote.insert(discussion=discussion_id, user_info=user_id)
        discussion.upvotes = discussion.upvotes + 1
        discussion.update_record()
    return True

def submit_new_discussion():
    # get data
    title = request.vars.title
    description = request.vars.description
    kind = request.vars.kind
    date_added = datetime.now()
    page_num = request.vars.page_num
    added_by = session.user_id
    # Deal with hashtags
    concepts = set(re.findall(r"#(\w+)", description)) # From http://stackoverflow.com/questions/2527892/parsing-a-tweet-to-extract-hashtags-into-an-array-in-python
    concepts = set(re.findall(r"#(\w+)", title)).union(concepts)
    ids = []
    for c in concepts:
        ids.append(__insert_concept(c, page_num))
    # Validate TODO fancier validation, also at client side
    if not title or not description:# or not kind:
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
    # update points for user
    user = db(db.user_info.id == added_by).select().first()
    user.contribution_points = user.contribution_points + ADD_DISCUSSION_POINTS
    user.update_record()
    # Update in session
    session.contribution_points = user.contribution_points
    # Send push notification
    __push_notification('notification', dict(
        event=EVENTS['new_discussion'], 
        user=session.user_name, 
        body=title,
        id=discussion_id,
        page=page_num,
        timestamp=str(date_added)))
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
        (db.discussion_message.added_by == db.user_info.id)).select(orderby=db.discussion_message.date_added)
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
    
    classified_messages = db(db.message_classification.classified_by == current_user_id).select(db.message_classification.discussion_message)
    # turn into a convenient format for the view
    ct_dict = dict()
    for ct in completed_tasks:
        if ct.associated_to not in ct_dict.keys():
            ct_dict[ct.associated_to] = []
        ct_dict[ct.associated_to].append(ct.task_definition)
    print(ct_dict)

    cl_msg = set()
    for cm in classified_messages:
        cl_msg.add(cm.discussion_message)
    # return
    return dict(
        discussion_id=id, 
        user_name=session.user_name, 
        current_user_id=current_user_id, 
        discussion=discussion, 
        discussion_messages=discussion_messages, 
        tasks=tasks,
        contribution_points=session.contribution_points, 
        page_num=discussion.page_num,
        completed_tasks=ct_dict,
        classified_messages=cl_msg)

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
    # Get discussion title
    title = db(db.discussion.id == discussion_id).select(db.discussion.title).first().title
    # Send notification
    __push_notification('notification', dict(
        event=EVENTS['new_comment'], 
        user=session.user_name, 
        userId=session.user_id,
        title=title,
        id=discussion_id,
        replyId=reply_id,
        body=message,
        timestamp=str(date_added)))
    
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
    task = db(db.task_definition.id == task_definition_id).select(db.task_definition.task_template).first()
    results = []
    for a in answers:
        results += a.user_input
    return json.dumps(dict(task=task.task_template, results=results))

def classify_reply():
    reply_id = request.vars['id']
    classification = request.vars['classification']
    reply_author = request.vars['reply_author']
    user = session.user_id

    # Create row
    db.message_classification.insert(
        discussion_message = reply_id,
        classified_by = user,
        classification = classification)

    # Update reply classification count
    reply = db(db.discussion_message.id == reply_id).select().first()
    count = reply.classification_count + 1
    reply.classification_count = count
    if count >= CLASSIFICATION_THRESHOLD:
        reply.classified = True
        classifications = db(db.message_classification.discussion_message == reply_id).select(db.message_classification.classification)
        classifications = [c.classification for c in classifications]
        __update_user_stats(reply_author, classifications)
    reply.update_record()

def get_user_stats():
    user = db(db.user_info.id == session.user_id).select().first()
    return json.dumps(dict(p_nont=user.p_nont, p_repr=user.p_repr, p_oper=user.p_oper))

def testws():
    __push_notification("notification", "something")


def __update_user_stats(user, classifications):
    print('Updating user ' + user)
    user = db(db.user_info.id == user).select().first()
    print(classifications)
    # Count
    count = defaultdict(int)
    for c in classifications:
        count[c] += 1
    classification = max(count.iteritems(), key=operator.itemgetter(1))[0]
    print(classification)

    # Define overall classification
    if classification.startswith('OPER'):
        user.p_oper = user.p_oper + 1
    elif classification.startswith('REPR'):
        user.p_repr = user.p_repr + 1
    else:
        user.p_nont = user.p_nont + 1
    user.update_record()


def __push_notification(type, data):
    websocket_send(
        'http://127.0.0.1:8888', 
        json.dumps(dict(type=type,data=data)), 
        'mykey', 
        'mygroup')
    return 0

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