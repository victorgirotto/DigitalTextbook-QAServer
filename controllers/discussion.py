import json

def page():
    page_num = request.vars.page_num
    # Validating params
    if not page_num:
        # Mandatory param was not found
        response.status = 500
        return 'You must supply a page_num param'

    # Retrieve discussions for page page_num
    results = db(db.discussion.page_num == page_num).select()
    discussions = [
        dict(id=r.id,
            title=r.title,
            added_by=r.added_by,
            date_added=str(r.date_added)) 
        for r in results]
        
    # return results
    response.headers['Content-Type'] = 'text/json'
    return json.dumps(discussions)

def discussion():
    discussion_id = request.vars.id
    # Validating params
    if not discussion_id:
        # Mandatory param was not found
        response.status = 500
        return 'You must supply the id param'
    
    # Retrieve discussion and its messages
    discussion = db(db.discussion.id == discussion_id).select().first()
    message_results = db(db.discussion_message.discussion == discussion_id).select(orderby=db.discussion_message.date_added)
    output = dict(
        discussion=dict(
            id=discussion.id, 
            title=discussion.title, 
            description=discussion.description),
        messages=[dict(
            message_content=m.message_content,
            date_added=str(m.date_added),
            added_by=m.added_by)
            for m in message_results])

    # Response        
    response.headers['Content-Type'] = 'text/json'
    return json.dumps(output)