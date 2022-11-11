#!/usr/bin/env python2.7

"""
Columbia W4111 Intro to databases
Example webserver

To run locally

    python server.py

Go to http://localhost:8111 in your browser


A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""

import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response, abort, session, flash, url_for

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)


# XXX: The Database URI should be in the format of: 
#
#     postgresql://USER:PASSWORD@<IP_OF_POSTGRE_SQL_SERVER>/<DB_NAME>
#
# For example, if you had username ewu2493, password foobar, then the following line would be:
#
#     DATABASEURI = "postgresql://ewu2493:foobar@<IP_OF_POSTGRE_SQL_SERVER>/postgres"
#
# For your convenience, we already set it to the class database

# Use the DB credentials you received by e-mail
DB_USER = "jfu2001"
DB_PASSWORD = "joshshimondatabase"

DB_SERVER = "w4111.cisxo09blonu.us-east-1.rds.amazonaws.com"

DATABASEURI = "postgresql://"+DB_USER+":"+DB_PASSWORD+"@"+DB_SERVER+"/proj1part2"


#
# This line creates a database engine that knows how to connect to the URI above
#
engine = create_engine(DATABASEURI)


# Here we create a test table and insert some values in it
engine.execute("""DROP TABLE IF EXISTS test;""")
engine.execute("""CREATE TABLE IF NOT EXISTS test (
  id serial,
  name text
);""")
engine.execute("""INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace');""")



@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request 
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request

  The variable g is globally accessible
  """
  try:
    g.conn = engine.connect()
  except:
    print("uh oh, problem connecting to database")
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass


#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to e.g., localhost:8111/foobar/ with POST or GET then you could use
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
# 
# see for routing: http://flask.pocoo.org/docs/0.10/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#


######### LOG IN - LOG OUT ###########

'''
@app.route('/')
def home():
    if not session.get('logged_in'):
        return render_template('login.html')
    else:
        context = dict(name = session['email'])
        return render_template("posts.html", **context)
'''
@app.route('/')
def home():
    if not session.get('logged_in'):
        return render_template('login.html')
    else:
        return redirect('/posts')
        
@app.route('/posts')
def posts():
    cmd = 'SELECT * FROM Products_Posted WHERE user_email != (:email1)';
    cursor = g.conn.execute(text(cmd), email1 = session['email']);
    posts = cursor.fetchall()
    context = dict(posts=posts)
    return render_template("posts.html", **context)

@app.route('/login', methods=['POST'])
def do_admin_login():
    email = request.form['email']
    password = request.form['password']
    cmd = 'SELECT password FROM Users WHERE email = (:email1)';
    cursor = g.conn.execute(text(cmd), email1 = email);
    passes = cursor.fetchall()
    if len(passes) > 0 and request.form['password'] == passes[0][0]:
        session['logged_in'] = True
        session['email'] = email
    else:
        flash('Invalid login credentials!')
    return redirect('/')

@app.route('/logout')
def logout():
    session['logged_in'] = False
    return redirect('/')

@app.route('/newaccount')
def new_account():
    return render_template('newaccount.html')

@app.route('/createnewaccount', methods=['POST'])
def create_new_account():
    values = []
    values.append(request.form['email'])
    values.append(request.form['fullname'])
    values.append(request.form['uni'])
    values.append(request.form['password'])
    values.append(request.form['venmo'])
    values.append(request.form['cashapp'])
    values.append(request.form['image'])
    values = clear_null_entries(values)
    try:
        cmd = 'INSERT INTO Users VALUES (:email1, :password1, :fullname1, :uni1, :venmo1, :cashapp1, :image1)';
        c = g.conn.execute(text(cmd), email1 = values[0], password1 = values[3], fullname1 = values[1], 
                           uni1 = values[2], venmo1 = values[4], cashapp1 = values[5], image1 = values[6]);
        session['logged_in'] = True
        session['email'] = values[0]
        c.close()
        return redirect('/')
    except:
        flash('Error creating account! Ensure all fields are entered correctly.')
        return redirect('/newaccount')
        
@app.route('/openpost', methods=['GET'])
def openpost():
    args = request.args
    pid = args.get("pid")
    cmd = 'SELECT * FROM Products_Posted WHERE product_id = (:pid1)';
    cursor = g.conn.execute(text(cmd), pid1 = pid);
    products = cursor.fetchall()
    context = dict(user_email = products[0][0], product_id = products[0][1], title = products[0][2], description = products[0][3], posted_date = products[0][4], product_type = products[0][5], image_url = products[0][6], tutoring_hourly_rate = products[0][7], tutoring_schedule = products[0][8], study_resource_price = products[0][9], study_resource_download_url = products[0][10])
    return render_template("post.html", **context)

##############################

@app.route('/myprofile')
def myprofile():
    cmd = 'SELECT * FROM Users WHERE email = (:email1)';
    c = g.conn.execute(text(cmd), email1 = session['email']);
    user_info = c.fetchall()
    c.close()
    context = dict(info = user_info)
    return render_template("myprofile.html", **context)


########### PROFILE ############

@app.route('/profile', methods=['GET'])
def profile():
    args = request.args
    uid = args.get("uid")
    
    cmd = 'SELECT follower_email FROM Followers WHERE user_email = (:uid1)';
    cursor = g.conn.execute(text(cmd), uid1 = uid);
    followers = cursor.fetchall()
    cursor.close()
    
    cmd = 'SELECT user_email FROM Followers WHERE follower_email = (:uid1)';
    cursor = g.conn.execute(text(cmd), uid1 = uid);
    followings = cursor.fetchall()
    cursor.close()
    
    cmd = 'SELECT * FROM Users WHERE email = (:uid1)';
    cursor = g.conn.execute(text(cmd), uid1 = uid);
    info = cursor.fetchall()
    cursor.close()
    
    cmd = 'SELECT * FROM Followers WHERE user_email = (:uid1) and follower_email = (:uid2)' ;
    cursor = g.conn.execute(text(cmd), uid1 = uid, uid2 = session['email']);
    print(uid)
    print(session['email'])
    flwer = cursor.fetchall()
    print(flwer)
    flw = 0
    if len(flwer) > 0:
        flw = 1
    
    context = dict(followers = followers, followings = followings, info = info, flw = flw)
    print(context)
    cursor.close()
    
    return render_template("profile.html", **context)

@app.route('/message', methods = ['GET'])
def message():
    args = request.args
    uid = args.get("uid")
    cmd = 'SELECT * FROM Messages_Sent_Received WHERE sender_email = (:sender1) AND receiver_email = (:sender2) OR sender_email = (:sender2) AND receiver_email = (:sender1)';
    c = g.conn.execute(text(cmd), sender1 = session['email'], sender2 = uid);
    messages = c.fetchall()
    context = dict(messages=messages)
    return render_template("messages.html", **context)

############## FOLLOW BUTTON ######


@app.route('/follow', methods=['GET'])
def follow():
    args = request.args
    uid = args.get("uid")
    try:
        cmd = 'INSERT INTO Followers VALUES (:user1, :follower1)';
        c = g.conn.execute(text(cmd), user1 = uid, follower1 = session['email']);
        c.close()
        return redirect(url_for('.profile', uid=uid))
    except:
        return redirect(url_for('.profile', uid=uid))
    

@app.route('/unfollow', methods=['GET'])
def unfollow():
    args = request.args
    uid = args.get("uid")
    try:
        cmd = 'DELETE FROM Followers WHERE user_email = :user1 and follower_email = :follower1';
        c = g.conn.execute(text(cmd), follower1 = uid, user1 = session['email']);
        c.close()
        return redirect(url_for('.profile', uid=uid))
    except:
        return redirect(url_for('.profile', uid=uid))



####################################

@app.route('/index')
def index():
  """
  request is a special object that Flask provides to access web request information:

  request.method:   "GET" or "POST"
  request.form:     if the browser submitted a form, this contains the data in the form
  request.args:     dictionary of URL arguments e.g., {a:1, b:2} for http://localhost?a=1&b=2

  See its API: http://flask.pocoo.org/docs/0.10/api/#incoming-request-data
  """

  # DEBUG: this is debugging code to see what request looks like
  print(request.args)


  #
  # example of a database query
  #
  cursor = g.conn.execute("SELECT name FROM test")
  names = []
  for result in cursor:
    names.append(result['name'])  # can also be accessed using result[0]
  cursor.close()

  #
  # Flask uses Jinja templates, which is an extension to HTML where you can
  # pass data to a template and dynamically generate HTML based on the data
  # (you can think of it as simple PHP)
  # documentation: https://realpython.com/blog/python/primer-on-jinja-templating/
  #
  # You can see an example template in templates/index.html
  #
  # context are the variables that are passed to the template.
  # for example, "data" key in the context variable defined below will be 
  # accessible as a variable in index.html:
  #
  #     # will print: [u'grace hopper', u'alan turing', u'ada lovelace']
  #     <div>{{data}}</div>
  #     
  #     # creates a <div> tag for each element in data
  #     # will print: 
  #     #
  #     #   <div>grace hopper</div>
  #     #   <div>alan turing</div>
  #     #   <div>ada lovelace</div>
  #     #
  #     {% for n in data %}
  #     <div>{{n}}</div>
  #     {% endfor %}
  #
  context = dict(data = names)


  #
  # render_template looks in the templates/ folder for files.
  # for example, the below file reads template/index.html
  #
  return render_template("index.html", **context)

#
# This is an example of a different path.  You can see it at
# 
#     localhost:8111/another
#
# notice that the functio name is another() rather than index()
# the functions for each app.route needs to have different names
#
@app.route('/another')
def another():
  return render_template("anotherfile.html")


# Example of adding new data to the database
@app.route('/add', methods=['POST'])
def add():
  name = request.form['name']
  print(name)
  cmd = 'INSERT INTO test(name) VALUES (:name1)';
  g.conn.execute(text(cmd), name1 = name);
  return redirect('/')



def clear_null_entries(values):
    for i in range(len(values)):
        if len(values[i]) == 0:
            values[i] = None
    return values
   




if __name__ == "__main__":
  import click

  app.secret_key = os.urandom(12)
  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using

        python server.py

    Show the help text using

        python server.py --help

    """

    HOST, PORT = host, port
    print("running on %s:%d" % (HOST, PORT))
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


  run()


