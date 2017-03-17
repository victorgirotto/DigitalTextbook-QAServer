def page():
    page_num = request.vars.page_num
    if not page_num:
        response.status = 500
        return 'You must supply a page_num param'
    return page_num

def discussion():
    discussion_id = request.vars.id
    return discussion_id