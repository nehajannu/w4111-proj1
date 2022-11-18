import os
  # accessible as a variable in index.html:
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response, url_for, session

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
app = Flask(__name__, template_folder=tmpl_dir, static_folder= static_dir)
app.secret_key = 'cs4111'

DATABASEURI = "postgresql://nj2439:6158@34.75.94.195/proj1part2"
engine = create_engine(DATABASEURI)

@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request.

  The variable g is globally accessible.
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
  If you don't, the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass

@app.route('/', methods=['GET','POST'])
def index():
  if session.get('logged_in') == True:
    #Handle search request
    if request.method == "POST":
      keyword = request.form['keyword']
      if keyword != "":
        return search(keyword)

    #Default: Show all items
    products = []
    cursor = g.conn.execute("SELECT * FROM product NATURAL JOIN belongs_to NATURAL JOIN category NATURAL JOIN listed_on NATURAL JOIN manages NATURAL JOIN cuuser")
    for result in cursor:
      products.append((result['productname'],result['productprice'],result['productimage'],result['categoryname'],result['username']))
    cursor.close()
    return render_template("index.html", products = products)
  
  #Redirect to login page if user is not logged in
  return redirect(url_for('login'))

#Sending search request to database
@app.route('/search')
def search(keyword):
  if session.get('logged_in') == True:
    products = []
    cursor = g.conn.execute("SELECT * FROM product NATURAL JOIN belongs_to NATURAL JOIN category WHERE productname = %s", keyword)
    for result in cursor:
      products.append((result['productname'],result['productprice'],result['productimage'],result['categoryname']))
    cursor.close()
    return render_template("index.html", products = products)
  
  #Redirect to login page if user is not logged in
  return redirect(url_for('login'))

#Logging users in
@app.route('/login', methods=['GET','POST'])
def login():
    error = ""
    if request.method == 'POST':
      cuid = request.form['cuid']
      cursor = g.conn.execute("SELECT password FROM cuuser WHERE cuid = %s", cuid)
      record = cursor.fetchall()
      cursor.close()

      if record:
        password = record[0]['password']
        if password == request.form['password']:
          #After successfully verifying, fetch user info from database
          cursor = g.conn.execute("SELECT * FROM cuuser NATURAL JOIN manages WHERE cuid = %s", cuid)
          user_record = cursor.fetchall()
          cursor.close()

          #Store user info in session, which will be kept until log out
          session['logged_in'] = True
          session['current_user'] = cuid
          user_info = user_record[0]
          session['username'] = user_info['username']
          session['userdescription'] = user_info['userdescription']
          session['profilepic'] = user_info['profilepic']
          session['storeid'] = user_info['storeid']
          return redirect(url_for('index'))
        else:
          error = 'Invalid cuid or password. Please try again'
      else:
        error = 'Invalid cuid or password. Please try again'
    return render_template('login.html', error=error)

#Logging users out
@app.route('/logout', methods=['GET','POST'])
def logout():
  session.pop('logged_in', None)
  session.pop('current_user', None)
  session.pop('username', None)
  session.pop('userdescription', None)
  session.pop('profilepic', None)
  session.pop('store_id', None)
  return render_template('login.html')

#User profile
@app.route('/profile', methods=['GET','POST'])
def profile():
  if session.get('logged_in') == True:
    
      cursor = g.conn.execute("SELECT productname, productprice, productimage FROM cuuser NATURAL JOIN manages NATURAL JOIN listed_on NATURAL JOIN product WHERE cuid = %s", session['current_user'])
      storefront_record = cursor.fetchall()
      cursor.close()
      #Default: Show all items
      storefront_products = []
      for result in storefront_record:
        storefront_products.append((result['productname'],result['productprice'],result['productimage']))
      return render_template("profile.html", storefront_products = storefront_products)

  return render_template('profile.html')
  
  #Redirect to login page if user is not logged in
  return redirect(url_for('login'))
    
#Server code for adding products to the storefront
@app.route('/save_name', methods = ['GET', 'POST'])
def save_name():
  if request.method == 'POST':
      if 'product-name' in request.form:
          productname = request.form['product-name']
      if 'product-price' in request.form:
          productprice = request.form['product-price']
      if 'product-image' in request.form:
          productimage = request.form['product-image']
    
if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):

    HOST, PORT = host, port
    print("running on %s:%d" % (HOST, PORT))
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)

  run()
