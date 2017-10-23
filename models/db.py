# -*- coding: utf-8 -*-
from datetime import datetime

# -------------------------------------------------------------------------
# This scaffolding model makes your app work on Google App Engine too
# File is released under public domain and you can use without limitations
# -------------------------------------------------------------------------

if request.global_settings.web2py_version < "2.14.1":
    raise HTTP(500, "Requires web2py 2.13.3 or newer")

# -------------------------------------------------------------------------
# if SSL/HTTPS is properly configured and you want all HTTP requests to
# be redirected to HTTPS, uncomment the line below:
# -------------------------------------------------------------------------
# request.requires_https()

# -------------------------------------------------------------------------
# app configuration made easy. Look inside private/appconfig.ini
# -------------------------------------------------------------------------
from gluon.contrib.appconfig import AppConfig

# -------------------------------------------------------------------------
# once in production, remove reload=True to gain full speed
# -------------------------------------------------------------------------
myconf = AppConfig(reload=True)

if not request.env.web2py_runtime_gae:
    # ---------------------------------------------------------------------
    # if NOT running on Google App Engine use SQLite or other DB
    # ---------------------------------------------------------------------
    db = DAL(myconf.get('db.uri'),
             pool_size=myconf.get('db.pool_size'),
             migrate_enabled=myconf.get('db.migrate'),
             check_reserved=['mysql'])
else:
    # ---------------------------------------------------------------------
    # connect to Google BigTable (optional 'google:datastore://namespace')
    # ---------------------------------------------------------------------
    db = DAL('google:datastore+ndb')
    # ---------------------------------------------------------------------
    # store sessions and tickets there
    # ---------------------------------------------------------------------
    session.connect(request, response, db=db)
    # ---------------------------------------------------------------------
    # or store session in Memcache, Redis, etc.
    # from gluon.contrib.memdb import MEMDB
    # from google.appengine.api.memcache import Client
    # session.connect(request, response, db = MEMDB(Client()))
    # ---------------------------------------------------------------------

# -------------------------------------------------------------------------
# by default give a view/generic.extension to all actions from localhost
# none otherwise. a pattern can be 'controller/function.extension'
# -------------------------------------------------------------------------
response.generic_patterns = ['*'] if request.is_local else []
# -------------------------------------------------------------------------
# choose a style for forms
# -------------------------------------------------------------------------
response.formstyle = myconf.get('forms.formstyle')  # or 'bootstrap3_stacked' or 'bootstrap2' or other
response.form_label_separator = myconf.get('forms.separator') or ''

# -------------------------------------------------------------------------
# (optional) optimize handling of static files
# -------------------------------------------------------------------------
# response.optimize_css = 'concat,minify,inline'
# response.optimize_js = 'concat,minify,inline'

# -------------------------------------------------------------------------
# (optional) static assets folder versioning
# -------------------------------------------------------------------------
# response.static_version = '0.0.0'

# -------------------------------------------------------------------------
# Here is sample code if you need for
# - email capabilities
# - authentication (registration, login, logout, ... )
# - authorization (role based authorization)
# - services (xml, csv, json, xmlrpc, jsonrpc, amf, rss)
# - old style crud actions
# (more options discussed in gluon/tools.py)
# -------------------------------------------------------------------------

from gluon.tools import Auth, Service, PluginManager

# host names must be a list of allowed host names (glob syntax allowed)
auth = Auth(db, host_names=myconf.get('host.names'))
service = Service()
plugins = PluginManager()

# -------------------------------------------------------------------------
# create all tables needed by auth if not custom tables
# -------------------------------------------------------------------------
# auth.define_tables(username=False, signature=False)

# -------------------------------------------------------------------------
# configure email
# -------------------------------------------------------------------------
mail = auth.settings.mailer
mail.settings.server = 'logging' if request.is_local else myconf.get('smtp.server')
mail.settings.sender = myconf.get('smtp.sender')
mail.settings.login = myconf.get('smtp.login')
mail.settings.tls = myconf.get('smtp.tls') or False
mail.settings.ssl = myconf.get('smtp.ssl') or False

# -------------------------------------------------------------------------
# configure auth policy
# -------------------------------------------------------------------------
auth.settings.registration_requires_verification = False
auth.settings.registration_requires_approval = False
auth.settings.reset_password_requires_verification = True

# -------------------------------------------------------------------------
# Define your tables below (or better in another model file) for example
#
# >>> db.define_table('mytable', Field('myfield', 'string'))
#
# Fields can be 'string','text','password','integer','double','boolean'
#       'date','time','datetime','blob','upload', 'reference TABLENAME'
# There is an implicit 'id integer autoincrement' field
# Consult manual for more options, validators, etc.
#
# More API examples for controllers:
#
# >>> db.mytable.insert(myfield='value')
# >>> rows = db(db.mytable.myfield == 'value').select(db.mytable.ALL)
# >>> for row in rows: print row.id, row.myfield
# -------------------------------------------------------------------------

# -------------------------------------------------------------------------
# after defining tables, uncomment below to enable auditing
# -------------------------------------------------------------------------
# auth.enable_record_versioning(db)

db.define_table('user_info',
    Field('name','string'),
    Field('date_added','datetime'),
    Field('contribution_points', 'integer'),
    Field('p_nont', 'integer', default=0),
    Field('p_repr', 'integer', default=0),
    Field('p_oper', 'integer', default=0))

db.define_table('discussion', 
    Field('title', 'string'),
    Field('kind', 'string'),
    Field('description', 'string'),
    Field('page_num', 'integer'),
    Field('added_by','reference user_info'),
    Field('date_added','datetime'),
    Field('upvotes','integer', default=0))

db.define_table('discussion_message',
    Field('discussion', 'reference discussion'),
    Field('message_content','string'),
    Field('date_added','datetime'),
    Field('added_by','reference user_info'),
    Field('classification_count', 'integer', default=0),
    Field('classified','boolean', default=False),
    Field('badges','list:reference task_definition'))

db.define_table('message_classification',
    Field('discussion_message', 'reference discussion_message'),
    Field('classified_by', 'reference user_info'),
    Field('classification', 'string'))

db.define_table('concept',
    Field('name','string'),
    Field('related_pages','list:integer'),
    Field('color','string'))

db.define_table('concept_discussion',
    Field('concept','reference concept'),
    Field('discussion','reference discussion'))

db.define_table('upvote',
    Field('discussion','reference discussion'),
    Field('user_info','reference user_info'))

'''
db.task_template.task_template syntax examples:
- Basic text input: {type:'text', label:'Label that will be shown before the input'}
'''
db.define_table('task_definition',
    Field('name', 'string'), # Task name
    Field('task_type', 'string'), # To which element is this task associated to: discussion reply, discussion itself, tagging, etc.
    Field('icon', 'string'), # Icon to be displayed
    Field('color', 'string'), # color of the badge
    Field('points', 'integer'), # How many points this task is worth 
    Field('threshold', 'integer'),
    Field('task_template', 'list:string')) # list of strings defining the structure of the task, i.e. what needs to be done. See below for syntax

# This table is basically an instance of the task_definition table, as completed by an individual user
db.define_table('task',
    Field('associated_to', 'integer'), # Id of the individual element it is associated to
    Field('task_definition', 'reference task_definition'),
    Field('user_input', 'list:string'),
    Field('completed_by', 'reference user_info'))

db.define_table('log',
    Field('timestamp', 'datetime', default=lambda:datetime.now()),
    Field('user', 'reference user_info'),
    Field('action', 'string'),
    Field('info', 'string'))