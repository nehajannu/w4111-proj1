import os
  # accessible as a variable in index.html:
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, flash, render_template, g, redirect, Response, url_for, session
import string
import random

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

#Generate random id for store, product, and order
def id_generator(length=10, c=string.digits):
  return ''.join(random.choice(c) for _ in range(length))

#Home page or search product page
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

#Creating a new account
@app.route('/signup', methods=['GET','POST'])
def signup():
  return render_template("signup.html")

#User profile
@app.route('/profile', methods=['GET','POST'])
def profile():
  if session.get('logged_in') == True:
    cursor = g.conn.execute("SELECT productid, productname, productprice, productimage FROM cuuser NATURAL JOIN manages NATURAL JOIN listed_on NATURAL JOIN product WHERE cuid = %s", session['current_user'])
    storefront_record = cursor.fetchall()
    cursor.close()
    #Show all items that the user has listed
    storefront_products = []
    for result in storefront_record:
      storefront_products.append((result['productname'],result['productprice'],result['productimage'],result['productid']))
    return render_template("profile.html", storefront_products = storefront_products)
  
  #Redirect to login page if user is not logged in
  return redirect(url_for('login'))

#Update user profile
@app.route('/settings', methods=['GET','POST'])
def settings():
  if session.get('logged_in') == True:
    return render_template("signup.html")
  #Redirect to login page if user is not logged in
  return redirect(url_for('login'))

#Add payment method
@app.route('/payment', methods=['GET','POST'])
def payment():
  if session.get('logged_in') == True:
    return render_template("payment.html")
  #Redirect to login page if user is not logged in
  return redirect(url_for('login'))

#Shopping cart
@app.route('/cart', methods=['GET','POST'])
def cart():
  if session.get('logged_in') == True:
    return render_template("cart.html")
  #Redirect to login page if user is not logged in
  return redirect(url_for('login'))

#Server code for adding products to the storefront
@app.route('/add_product', methods = ['GET', 'POST'])
def add_product():
  if session.get('logged_in') == True:
    if request.method == 'POST':
      productid = id_generator()
      productname = request.form['product-name']
      productprice = request.form['product-price']
      productdescription = request.form['product-description']
      productimage = request.form['product-image']
      categoryid = request.form['product-category']

      #Add product to database
      cursor = g.conn.execute("INSERT INTO product VALUES(%s,%s,%s,%s,%s)",productid, productname, productprice, productdescription, productimage)
      cursor.close()
      #Add product to category (belongs_to relationship)
      cursor = g.conn.execute("INSERT INTO belongs_to VALUES(%s,%s)",productid, categoryid)
      cursor.close()
      #Add product to storefront (listed_on relationship)
      cursor = g.conn.execute("INSERT INTO listed_on VALUES(%s,%s)",productid, session['storeid'])
      cursor.close()

      flash('Item successfully added!','success')
      
      return redirect(url_for('profile'))
    return render_template('add_product.html')

  #Redirect to login page if user is not logged in
  return redirect(url_for('login'))

#Server code for adding products to the storefront
@app.route('/delete_product', methods = ['GET', 'POST'])
def delete_product():
  if session.get('logged_in') == True:
    if request.method == 'POST':
      productid = request.form['delete-product']

      #Remove product from category (belongs_to relationship)
      cursor = g.conn.execute("DELETE FROM belongs_to WHERE productid = %s",productid)
      cursor.close()
      #Remove product from storefront (listed_on relationship)
      cursor = g.conn.execute("DELETE FROM listed_on WHERE productid = %s",productid)
      cursor.close()
      #Remove product from database
      cursor = g.conn.execute("DELETE FROM product WHERE productid = %s",productid)
      cursor.close()

      flash('Item successfully removed!','success')
      
      return redirect(url_for('profile'))

  #Redirect to login page if user is not logged in
  return redirect(url_for('login'))

  #Server Code for Price Filter 
  @app.route("/pricefilter",methods=["POST","GET"])
  def pricefilter():
    if session.get('logged_in') == True:
      cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
      if request.method == 'POST':
        query = request.form['action']
        minimum_price = request.form['minimum_price']
        maximum_price = request.form['maximum_price']
        #print(query)
        if query == '':
          cur.execute("SELECT * FROM product ORDER BY product-name ASC")
          productlist = cur.fetchall()
          cursor.close()
          print('all list')
        else:
          cur.execute("SELECT * FROM product WHERE product-price BETWEEN (%s) AND (%s)", [minimum_price, maximum_price])
          productlist = cur.fetchall()  
          cursor.close()
          
        return render_template("index.html")
    
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
