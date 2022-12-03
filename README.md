# 4111 Introduction to Databases: Columbia Buy & Sell
<p align="center"><img width="600" alt="image" align="center" src="https://user-images.githubusercontent.com/66938562/205405325-1754f788-a694-465e-88e5-49e5ecb899c2.png"></p>

### <p align="center">This project was chosen by Professor Gravano as a winner of the COMS4111 project competition</p>

## About
We want to create a database that emulates the Facebook marketplace page for Columbia Buy & Sell. The domain is to provide an interface that allows students to easily list, search, and purchase items on campus. After signing up with a valid CUID, student can buy and sell items on the website. One portion of the application would allow the user to add a product to a storefront for the other users of the application to see. The other portion would resemble an online shopping website's interface where each product has a category attached to it, making it easier for users to find what they are looking for. 

### Run the application
<code>python3 server.py</code>

### Languages and Frameworks
<p align="center">
 <!--Python-->
<code><img height="30" width:"30" src="https://img.shields.io/badge/python-%233776AB.svg?&style=flat-square&logo=python&logoColor=white" /></code>
<!--Flask-->
<code><img height="30" width:"30" src="https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white" /></code>
<!--PostgreSQL-->
<code><img height="30" width:"30" src="https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white" /></code>
<!--Google Cloud-->
<code><img height="30" width:"30" src="https://img.shields.io/badge/GoogleCloud-%234285F4.svg?style=for-the-badge&logo=google-cloud&logoColor=white" /></code>
</p>

## Functionalities
### Search page
<img width="1200" alt="image" src="https://user-images.githubusercontent.com/66938562/205403250-e53ef560-9b1f-4241-9ef4-e32ce4d3ed44.png">

### Profile page
<img width="1200" alt="image" src="https://user-images.githubusercontent.com/66938562/205403567-efa265f3-b26b-44fe-8325-a1cd9820eff3.png">

## Database Design
<img width="1400" alt="Screen Shot 2022-12-02 at 6 17 23 PM" src="https://user-images.githubusercontent.com/66938562/205409795-16a93550-5534-4df6-a582-996a4f214efc.png">

### Entity Schema
    CREATE TABLE Storefront 
      (  storeid VARCHAR(32),
         storeitemcount INTEGER,
         PRIMARY KEY (storeid))
      
    CREATE TABLE Product 
      (  productid VARCHAR(32),
         productname VARCHAR(50) CHECK (LENGTH(productname) >= 1),
         productprice FLOAT CONSTRAINT positive_price CHECK (productprice > 0),
         productdescription VARCHAR(200),
         productimage VARCHAR(500),
         PRIMARY KEY (productid))
          
    CREATE TABLE Category
      (  categoryid VARCHAR(32),
         categoryname VARCHAR(50) CHECK (length(categoryname) >= 1),
         PRIMARY KEY (categoryid))
          
    CREATE TABLE CUUser
      (  cuid VARCHAR(10), 
         username VARCHAR(100) CHECK (length(username) >= 1),
         profilepic VARCHAR(500), 
         userdescription VARCHAR(200),
         PRIMARY KEY (cuid))
    
    CREATE TABLE Payment
      (  creditcardno CHAR(16), 
         creditcardholder varchar(100) CHECK (length(creditcardholder) >= 1),
         creditcardexpdate DATE CONSTRAINT check_date CHECK (creditcardexpdate >= CURRENT_DATE),
         PRIMARY KEY (creditcardno))

### Relationship Schema
(Participation constraints not capture)

    CREATE TABLE Listed_On
      (  productid VARCHAR(32),
         storeid VARCHAR(32),
         PRIMARY KEY (productid), 
         FOREIGN KEY (productid) 
           REFERENCES Product
             ON DELETE CASCADE
             ON UPDATE CASCADE,
         FOREIGN KEY (storeid) 
           REFERENCES Storefront)
    
    CREATE TABLE Belongs_To
      (  productid VARCHAR(32),
         categoryid VARCHAR(32),
         PRIMARY KEY (productid, categoryid), 
         FOREIGN KEY (productid)
           REFERENCES Product
             ON DELETE CASCADE
             ON UPDATE CASCADE,
         FOREIGN KEY (categoryid)
           REFERENCES Category)
           
    CREATE TABLE Manages
      (  cuid VARCHAR(10) NOT NULL,
         storeid VARCHAR(32),
         PRIMARY KEY (storeid), 
         UNIQUE (cuid),
         FOREIGN KEY (cuid) 
           REFERENCES CUUser,
         FOREIGN KEY (storeid) 
           REFERENCES Storefront)

    CREATE TABLE Adds_To 
      (  productid VARCHAR(32),
         orderid VARCHAR(32),
         PRIMARY KEY (productid, orderid), 
         FOREIGN KEY (productid) 
           REFERENCES Product
             ON DELETE CASCADE
             ON UPDATE CASCADE,
         FOREIGN KEY (orderid) 
           REFERENCES Order_Placed)

    CREATE TABLE Has 
      (  creditcardno VARCHAR(16),
         cuid VARCHAR(10),
         PRIMARY KEY (creditcardno, cuid), 
         FOREIGN KEY (creditcardno) 
           REFERENCES Payment
             ON DELETE CASCADE
             ON UPDATE CASCADE,
         FOREIGN KEY (cuid) 
           REFERENCES CUUser)
           
    CREATE TABLE Order_Placed
      (  orderid CHAR(32),
         orderitemcount INTEGER CHECK (orderitemcount > 0),
         ordertotalprice FLOAT CONSTRAINT positive_price CHECK (ordertotalprice > 0),
         dateordered DATE CONSTRAINT check_date CHECK (dateordered <= CURRENT_DATE),
         cuid CHAR(10) NOT NULL,
         PRIMARY KEY (orderid),
         FOREIGN KEY (cuid) 
           REFERENCES CUUser)

## Team members
Josephine (Chiao Fen) Chan
Neha Jannu
