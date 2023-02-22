from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow 
from datetime import datetime
import os

# Init app
app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
# Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'db.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

with app.app_context():
# Init db
    db = SQLAlchemy(app)
# Init ma
ma = Marshmallow(app)

# Product Class/Model
class Product(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(100), unique=True)
  description = db.Column(db.String(200))
  price = db.Column(db.Float)
  qty = db.Column(db.Integer)
  #a product can have many reviews
  reviews = db.relationship(
        "Review", backref=db.backref("product", lazy="joined"), lazy="select"
    )

  def __init__(self, name, description, price, qty):
    self.name = name
    self.description = description
    self.price = price
    self.qty = qty

  def to_json(self):
    return {
      "id": self.id,
      "name": self.name,
      "description": self.description,
      "price": self.price,
      "quantity": self.qty,
      "reviews": [{"id": r.id, "review": r.text, "reviewerId": r.user_id, "reviewerName": r.getReviewer() } for r in self.reviews] if self.reviews else None
    }

#REviews
class Review(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  text = db.Column(db.String(100))
  date_created = db.Column(db.DateTime, default=datetime.utcnow)
  user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
  product_id =  db.Column(db.Integer, db.ForeignKey("product.id"))

  def __init__(self, text, user_id, product_id):
    self.text = text
    self.user_id = user_id
    self.product_id = product_id
  def getReviewer(self):
    user = User.query.get(self.user_id)
    return user.name if user else None

#User
class User(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(100), unique=True)
  # A user can have many reviews
  reviews = db.relationship(
        "Review", backref=db.backref("user", lazy="joined"), lazy="select"
    )
  def __init__(self, name):
    self.name = name


# Product Schema
class ProductSchema(ma.Schema):
  class Meta:
    fields = ('id', 'name', 'description', 'price', 'qty')

# Init schema
product_schema = ProductSchema()
products_schema = ProductSchema(many=True)

# Review Schema
class ReviewSchema(ma.Schema):
  class Meta:
    fields = ('text', 'date_created')

# Init schema
review_schema = ReviewSchema()
reviews_schema = ReviewSchema(many=True)

# User Schema
class UserSchema(ma.Schema):
  class Meta:
    fields = ('id', 'name')

# Init schema
user_schema = UserSchema()
users_schema = UserSchema(many=True)

# Create a Product
@app.route('/product', methods=['POST'])
def add_product():
  name = request.json['name']
  description = request.json['description']
  price = request.json['price']
  qty = request.json['qty']

  new_product = Product(name, description, price, qty)

  db.session.add(new_product)
  db.session.commit()

  return product_schema.jsonify(new_product)

# Create a Review
@app.route('/review/product/<pid>/user/<uid>', methods=['POST'])
def add_review(pid, uid):
  text = request.json['text']
  new_review = Review(text, uid, pid)

  db.session.add(new_review)
  db.session.commit()

  return review_schema.jsonify(new_review)


# Create a User
@app.route('/user', methods=['POST'])
def add_user():
  name = request.json['name']
  new_user = User(name)

  db.session.add(new_user)
  db.session.commit()

  return user_schema.jsonify(new_user)

# Get All Products
@app.route('/product', methods=['GET'])
def get_products():
  all_products = Product.query.all()
  result = products_schema.dump(all_products)
  return jsonify(result)

# Get Single Products
@app.route('/product/<id>', methods=['GET'])
def get_product(id):
  product = Product.query.get(id)
  #return product_schema.jsonify(product)
  return jsonify(product.to_json())

# Update a Product
@app.route('/product/<id>', methods=['PUT'])
def update_product(id):
  product = Product.query.get(id)

  name = request.json['name']
  description = request.json['description']
  price = request.json['price']
  qty = request.json['qty']

  product.name = name
  product.description = description
  product.price = price
  product.qty = qty

  db.session.commit()

  return product_schema.jsonify(product)

# Delete Product
@app.route('/product/<id>', methods=['DELETE'])
def delete_product(id):
  product = Product.query.get(id)
  db.session.delete(product)
  db.session.commit()

  return product_schema.jsonify(product)

# Run Server
if __name__ == '__main__':
  app.run(debug=True)