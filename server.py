import os
  # accessible as a variable in index.html:
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response, url_for

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
app = Flask(__name__, template_folder=tmpl_dir, static_folder= static_dir)

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
  """
  request is a special object that Flask provides to access web request information:

  request.method:   "GET" or "POST"
  request.form:     if the browser submitted a form, this contains the data in the form
  request.args:     dictionary of URL arguments, e.g., {a:1, b:2} for http://localhost?a=1&b=2

  See its API: https://flask.palletsprojects.com/en/2.0.x/api/?highlight=incoming%20request%20data

  """

  #Handle search request
  if request.method == "POST":
    keyword = request.form['keyword']
    if keyword != "":
      return search(keyword)

  #Default: Show all items
  products = []
  cursor = g.conn.execute("SELECT * FROM product NATURAL JOIN belongs_to NATURAL JOIN category")
  for result in cursor:
    products.append((result['productname'],result['productprice'],result['productimage'],result['categoryname']))
  cursor.close()
  return render_template("index.html", products = products)

#Logging users in
@app.route('/login', methods=['GET','POST'])
def login():
    error = None
    if request.method == 'POST':
      cuid = request.form['cuid']
      cursor = g.conn.execute("SELECT password FROM cuuser WHERE cuid = %s", cuid)
      record = cursor.fetchall()
      cursor.close()
      password = record[0]['password']

      if password and password == request.form['password']:
        return redirect(url_for('index'))
      else:
        error = 'Invalid cuid or password. Please try again'
    return render_template('login.html', error=error)
    
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
    
#Sending search request to database
@app.route('/search')
def search(keyword):
  products = []
  cursor = g.conn.execute("SELECT * FROM product NATURAL JOIN belongs_to NATURAL JOIN category WHERE productname = %s", keyword)
  for result in cursor:
    products.append((result['productname'],result['productprice'],result['productimage'],result['categoryname']))
  cursor.close()
  return render_template("index.html", products = products)

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
