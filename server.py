import os
  # accessible as a variable in index.html:
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, flash, render_template, g, redirect, Response, url_for, session
import string
import random
import datetime

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
      category_filter = request.form['category-filter']
      price_sort = request.form['price-sort']
      return search(keyword, category_filter, price_sort)

    #Default: Show all items
    products = []
    cursor = g.conn.execute("SELECT * FROM product NATURAL JOIN belongs_to NATURAL JOIN category NATURAL JOIN listed_on NATURAL JOIN manages NATURAL JOIN cuuser")
    for result in cursor:
      products.append((result['productname'],result['productprice'],result['productimage'],result['categoryname'],result['username'],result['productid'],result['sold'],result['cuid']))
    cursor.close()
    return render_template("index.html", products = products)
  
  #Redirect to login page if user is not logged in
  return redirect(url_for('login'))

#Sending search request to database
@app.route('/search')
def search(keyword, category_filter, price_sort):
  if session.get('logged_in') == True:
    products = []
    #ASC
    if price_sort == 'ASC':
      #keyword and category are both unfilled
      if keyword == "" and category_filter == "all":
        cursor = g.conn.execute("SELECT * FROM product NATURAL JOIN belongs_to NATURAL JOIN category NATURAL JOIN listed_on NATURAL JOIN manages NATURAL JOIN cuuser ORDER BY \"productprice\" ASC")
      #keyword is filled but not category
      elif category_filter == "all":
        cursor = g.conn.execute("SELECT * FROM product NATURAL JOIN belongs_to NATURAL JOIN category NATURAL JOIN listed_on NATURAL JOIN manages NATURAL JOIN cuuser WHERE productname = %s ORDER BY \"productprice\" ASC", keyword)
      #category is filled but not keyword
      elif keyword == "":
        cursor = g.conn.execute("SELECT * FROM product NATURAL JOIN belongs_to NATURAL JOIN category NATURAL JOIN listed_on NATURAL JOIN manages NATURAL JOIN cuuser WHERE categoryname = %s ORDER BY \"productprice\" ASC", category_filter)
      #keyword and category are both filled
      else:
        cursor = g.conn.execute("SELECT * FROM product NATURAL JOIN belongs_to NATURAL JOIN category NATURAL JOIN listed_on NATURAL JOIN manages NATURAL JOIN cuuser WHERE productname = %s and categoryname = %s ORDER BY \"productprice\" ASC", keyword, category_filter)
    #DESC
    else:
      #keyword and category are both unfilled
      if keyword == "" and category_filter == "all":
        cursor = g.conn.execute("SELECT * FROM product NATURAL JOIN belongs_to NATURAL JOIN category NATURAL JOIN listed_on NATURAL JOIN manages NATURAL JOIN cuuser ORDER BY \"productprice\" DESC")
      #keyword is filled but not category
      elif category_filter == "all":
        cursor = g.conn.execute("SELECT * FROM product NATURAL JOIN belongs_to NATURAL JOIN category NATURAL JOIN listed_on NATURAL JOIN manages NATURAL JOIN cuuser WHERE productname = %s ORDER BY \"productprice\" DESC", keyword)
      #category is filled but not keyword
      elif keyword == "":
        cursor = g.conn.execute("SELECT * FROM product NATURAL JOIN belongs_to NATURAL JOIN category NATURAL JOIN listed_on NATURAL JOIN manages NATURAL JOIN cuuser WHERE categoryname = %s ORDER BY \"productprice\" DESC", category_filter)
      #keyword and category are both filled
      else:
        cursor = g.conn.execute("SELECT * FROM product NATURAL JOIN belongs_to NATURAL JOIN category NATURAL JOIN listed_on NATURAL JOIN manages NATURAL JOIN cuuser WHERE productname = %s and categoryname = %s ORDER BY \"productprice\" DESC", keyword, category_filter)

    for result in cursor:
      products.append((result['productname'],result['productprice'],result['productimage'],result['categoryname'], result['username'],result['productid'],result['sold'],result['cuid']))
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
          session['password'] = password
          user_info = user_record[0]
          session['username'] = user_info['username']
          session['userdescription'] = user_info['userdescription']
          session['profilepic'] = user_info['profilepic']
          session['storeid'] = user_info['storeid']
          session['cart'] = []
          session['total_price'] = 0
          session['profit'] = 0
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
    #Show all items that the user has listed
    cursor = g.conn.execute("SELECT productid, productname, productprice, productimage FROM cuuser NATURAL JOIN manages NATURAL JOIN listed_on NATURAL JOIN product WHERE cuid = %s", session['current_user'])
    storefront_record = cursor.fetchall()
    cursor.close()
    
    storefront_products = []
    for result in storefront_record:
      storefront_products.append((result['productname'],result['productprice'],result['productimage'],result['productid']))

    #Calculate the profit that a user has made
    cursor = g.conn.execute("SELECT productprice FROM manages NATURAL JOIN listed_on NATURAL JOIN product WHERE cuid = %s and sold = true", session['current_user'])
    total_profit = cursor.fetchall()
    cursor.close()
    session['profit'] = sum(profit[0] for profit in total_profit)

    return render_template("profile.html", storefront_products = storefront_products)
  
  #Redirect to login page if user is not logged in
  return redirect(url_for('login'))

#Update user profile
@app.route('/settings', methods=['GET','POST'])
def settings():
  if session.get('logged_in') == True:
    if request.method == 'POST':
      #Update user information
      username = request.form['username']
      password = request.form['password']
      userdescription = request.form['userdescription']
      profilepic = request.form['profilepic']
      cursor = g.conn.execute("UPDATE cuuser SET username =%s, password=%s, userdescription=%s, profilepic=%s WHERE cuid = %s", username, password, userdescription, profilepic, session['current_user'])
      cursor.close()
      session['username'] = username
      session['password'] = password
      session['userdescription'] = userdescription
      session['profilepic'] = profilepic

      #Show all items that the user has listed
      cursor = g.conn.execute("SELECT productid, productname, productprice, productimage FROM cuuser NATURAL JOIN manages NATURAL JOIN listed_on NATURAL JOIN product WHERE cuid = %s", session['current_user'])
      storefront_record = cursor.fetchall()
      cursor.close()
      storefront_products = []
      for result in storefront_record:
        storefront_products.append((result['productname'],result['productprice'],result['productimage'],result['productid']))
      return render_template("profile.html", storefront_products = storefront_products)
    return render_template("settings.html")

  #Redirect to login page if user is not logged in
  return redirect(url_for('login'))

#View payment method
@app.route('/payment', methods=['GET','POST'])
def payment():
  if session.get('logged_in') == True:
    cursor = g.conn.execute("SELECT * FROM payment NATURAL JOIN has WHERE cuid = %s", session['current_user'])
    payment_record = cursor.fetchall()
    cursor.close()
    
    #Show all payment methods that the user has added
    payment_methods = []
    for result in payment_record:
      payment_methods.append((result['creditcardno'],result['creditcardholder'],result['creditcardexpdate']))

    return render_template("payment.html", payment_methods = payment_methods)

  #Redirect to login page if user is not logged in
  return redirect(url_for('login'))

#Add payment method
@app.route('/add_payment', methods=['GET','POST'])
def add_payment():
  if session.get('logged_in') == True:
    if request.method == 'POST':
      creditcardno = request.form['creditcardno']
      creditcardholder = request.form['creditcardholder']
      creditcardexpdate = request.form['creditcardexpdate']

      #Make sure the same card number doesn't already exist for the user
      cursor = g.conn.execute("SELECT * FROM payment NATURAL JOIN has WHERE cuid = %s", session['current_user'])
      payment_record = cursor.fetchall()
      cursor.close()

      for result in payment_record:
        if result['creditcardno'] == creditcardno:
          return render_template('add_payment.html', error= "Cannot add the same card number twice")
    
      #Add credit card to database
      cursor = g.conn.execute("INSERT INTO payment VALUES(%s,%s,%s)",creditcardno, creditcardholder, creditcardexpdate)
      cursor.close()
      #Add credit card to user (has relationship)
      cursor = g.conn.execute("INSERT INTO has VALUES(%s,%s)",creditcardno,session['current_user'])
      cursor.close()

      flash('Payment method successfully added!','success')
      
      return redirect(url_for('payment'))
    return render_template('add_payment.html')

  #Redirect to login page if user is not logged in
  return redirect(url_for('login'))

#Delete payment method
@app.route('/delete_payment', methods = ['GET', 'POST'])
def delete_payment():
  if session.get('logged_in') == True:
    if request.method == 'POST':
      creditcardno = request.form['delete-payment']

      #Prevent deletion if there is only one payment method left
      cursor = g.conn.execute("SELECT * FROM payment NATURAL JOIN has WHERE cuid = %s", session['current_user'])
      payment_record = cursor.fetchall()
      cursor.close()
      if len(payment_record) <= 1:
        flash('Cannot delete your only payment method','error')
        return redirect(url_for('payment'))

      #Remove payment from user (has relationship)
      cursor = g.conn.execute("DELETE FROM has WHERE creditcardno = %s",creditcardno)
      cursor.close()
      #Remove payment from database
      cursor = g.conn.execute("DELETE FROM payment WHERE creditcardno = %s",creditcardno)
      cursor.close()

      flash('Payment successfully removed!','success')
      return redirect(url_for('payment'))

  #Redirect to login page if user is not logged in
  return redirect(url_for('login'))

#Shopping cart
@app.route('/cart', methods=['GET','POST'])
def cart():
  if session.get('logged_in') == True:
    #Fetch all the products in cart by productid 
    in_cart = session['cart']
    cart = []
    for pid in in_cart:
      cursor = g.conn.execute("SELECT * FROM product NATURAL JOIN belongs_to NATURAL JOIN category WHERE productid = %s", pid)
      record = cursor.fetchall()
      cursor.close()
      result = record[0]
      cart.append((result['productname'],result['productprice'],result['productimage'],result['productid']))

    return render_template("cart.html", cart=cart)
  #Redirect to login page if user is not logged in
  return redirect(url_for('login'))

@app.route('/add_cart', methods=['GET','POST'])
def add_cart():
  if session.get('logged_in') == True:
    #Save the product ids in session
    to_add = request.form['productid']
    in_cart = session['cart']
    #First check if the product is already added. if yes, stay on the index page with error message
    if to_add in in_cart:
      flash('This item is already in your cart','error')
      return redirect(url_for('index'))
    #Then check whether the product is sold by yourself. if yes prevent user from adding it into their cart
    cursor = g.conn.execute('SELECT * FROM listed_on WHERE productid = %s', to_add)
    same_store = cursor.fetchall()
    cursor.close()
    if same_store[0]['storeid'] == session['storeid']:
      flash('You cannot buy your own product','error')
      return redirect(url_for('index'))

    in_cart.append(to_add)
    session['cart'] = in_cart

    #Fetch all the products in cart by productid 
    cart = []
    price = 0
    for pid in in_cart:
      cursor = g.conn.execute("SELECT * FROM product NATURAL JOIN belongs_to NATURAL JOIN category WHERE productid = %s", pid)
      record = cursor.fetchall()
      cursor.close()
      result = record[0]
      cart.append((result['productname'],result['productprice'],result['productimage'],result['productid']))
      price += int(result['productprice'])

    session['total_price'] = price
    return render_template("cart.html", cart=cart)

  #Redirect to login page if user is not logged in
  return redirect(url_for('login'))

#Delete item in cart
@app.route('/delete_cart', methods=['GET','POST'])
def delete_cart():
  if session.get('logged_in') == True:
    to_delete = request.form['productid']
    in_cart = session['cart']
    in_cart.remove(to_delete)
    session['cart'] = in_cart

    #Fetch all the products in cart by productid 
    cart = []
    price = 0
    for pid in in_cart:
      cursor = g.conn.execute("SELECT * FROM product NATURAL JOIN belongs_to NATURAL JOIN category WHERE productid = %s", pid)
      record = cursor.fetchall()
      cursor.close()
      result = record[0]
      cart.append((result['productname'],result['productprice'],result['productimage'],result['productid']))
      price += int(result['productprice'])

    session['total_price'] = price

    return render_template("cart.html",cart = cart)

  #Redirect to login page if user is not logged in
  return redirect(url_for('login'))

#Checkout an order
@app.route('/checkout', methods=['GET','POST'])
def checkout():
  if session.get('logged_in') == True:
    if request.method == 'GET':
      cursor = g.conn.execute("SELECT * FROM payment NATURAL JOIN has WHERE cuid = %s", session['current_user'])
      payment_record = cursor.fetchall()
      cursor.close()

      #Show all payment methods that the user has added
      payment_methods = []
      for result in payment_record:
        payment_methods.append((result['creditcardno']))
      
      return render_template("checkout.html", cards = payment_methods)
    
    #POST request to add order
    orderid = id_generator()
    cart = session['cart']
    orderitemcount = len(cart)
    ordertotalprice = session['total_price']
    dateordered = str(datetime.datetime.now().date())
    cursor = g.conn.execute("INSERT INTO order_placed VALUES(%s,%s,%s,%s,%s)",orderid,orderitemcount,ordertotalprice,dateordered,session['current_user'])
    cursor.close()

    #Mark the products in this order as sold and record them as belonging to a specific order (adds_to relationship)
    for pid in cart:
      cursor = g.conn.execute("UPDATE product SET sold = true WHERE productid = %s", pid)
      cursor.close()
      cursor = g.conn.execute("INSERT INTO adds_to VALUES(%s,%s)",pid,orderid)
      cursor.close()

    #Clear cart after ordering
    session['cart'] = []
    session['total_price'] = 0

    flash('Successfully placed order!','success')
    return redirect(url_for('past_orders'))

  #Redirect to login page if user is not logged in
  return redirect(url_for('login'))

#Past orders
@app.route('/past_orders', methods=['GET','POST'])
def past_orders():
  if session.get('logged_in') == True:
    cursor = g.conn.execute('SELECT * FROM order_placed WHERE cuid = %s ORDER BY dateordered DESC',session['current_user'])
    order_record = cursor.fetchall()
    cursor.close()

    orders = []
    for result in order_record:
      #Get the product names that belong to each order
      cursor = g.conn.execute('SELECT * FROM adds_to NATURAL JOIN product WHERE orderid = %s',result['orderid'])
      products_in_order = cursor.fetchall()
      cursor.close()
      print(products_in_order)

      orders.append((result['orderid'],result['orderitemcount'],result['ordertotalprice'],result['dateordered'],products_in_order))
    return render_template("past_orders.html", orders=orders)

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

#Server code for deleting products to the storefront
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

#Seller storefront
@app.route('/storefront', methods=['GET','POST'])
def storefront():
  if session.get('logged_in') == True:
    #If there's no input, redirect to homepage
    seller_input = request.form.get('seller', None)
    if seller_input == None:
      return redirect(url_for('index'))

    #Grab seller information
    cursor = g.conn.execute("SELECT * FROM cuuser NATURAL JOIN manages WHERE cuid = %s", seller_input)
    seller_record = cursor.fetchall()
    cursor.close()

    seller_info = seller_record[0]
    seller = (seller_input, seller_info['username'],seller_info['userdescription'],seller_info['profilepic'])

    #Grab store information
    cursor = g.conn.execute("SELECT productid, productname, productprice, productimage FROM cuuser NATURAL JOIN manages NATURAL JOIN listed_on NATURAL JOIN product WHERE cuid = %s", seller_input)
    storefront_record = cursor.fetchall()
    cursor.close()
    #Show all items that the user has listed
    storefront_products = []
    for result in storefront_record:
      storefront_products.append((result['productname'],result['productprice'],result['productimage'],result['productid']))
    return render_template("storefront.html", storefront_products = storefront_products, seller=seller)
  
  #Redirect to login page if user is not logged in
  return redirect(url_for('login'))
    
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
