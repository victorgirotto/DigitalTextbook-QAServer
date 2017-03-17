import json

def concept():
    concept_id = request.vars.concept_id
    # Validating params
    if not concept_id:
        # Mandatory param was not found
        response.status = 500
        return 'You must supply the concept param'
    
    # Retrieve list of discussions that contain this concept
    results = db(
        (db.concept_discussion.concept == concept_id) &
        (db.discussion.id == db.concept_discussion.discussion)).select(groupby=db.discussion.id)
    discussions = [dict(
        id=d.discussion.id,
        title=d.discussion.title,
        added_by=d.discussion.added_by,
        date_added=str(d.discussion.date_added))
        for d in results]

    # Response        
    response.headers['Content-Type'] = 'text/json'
    return json.dumps(discussions)


