from flask_sqlalchemy import SQLAlchemy
from flask import Flask, request, jsonify
from flask_marshmallow import Marshmallow
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, Table, String, Column, select
from marshmallow import ValidationError
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from typing import List
from dotenv import load_dotenv
import os
from datetime import date

app = Flask(__name__)
load_dotenv()
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_NOTIFICATION'] = False

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
db.init_app(app)
ma = Marshmallow(app)


# Association Table

order_product = Table(
    "order_product",
    Base.metadata,
    Column("order_id", ForeignKey("orders.order_id")),
    Column("product_id", ForeignKey("products.prod_id"))
)

# Users Table

class User(Base):
    __tablename__ = 'users'

    user_id: Mapped[int] = mapped_column(primary_key=True, nullable=False)
    user_name: Mapped[str] = mapped_column(String(50), nullable=False)
    user_address: Mapped[str] = mapped_column(String(50))
    user_email: Mapped[str] = mapped_column(String(200), nullable=False)

    orders: Mapped[List['Order']] = relationship(back_populates='user')

# Orders Table

class Order(Base):
    __tablename__ = "orders"

    order_id: Mapped[int] = mapped_column(primary_key=True)
    order_date: Mapped[date] = mapped_column()
    user_id: Mapped[int] = mapped_column(ForeignKey('users.user_id'), nullable=False)

    products: Mapped[List['Product']] = relationship(secondary=order_product, back_populates='orders')
    user: Mapped['User'] = relationship(back_populates="orders")


# Products Table

class Product(Base):
    __tablename__ = "products"

    prod_id: Mapped[int] = mapped_column(primary_key=True)
    prod_name: Mapped[str] = mapped_column(String(100))
    prod_price: Mapped[int] = mapped_column()

    orders: Mapped[List['Order']] = relationship(secondary=order_product, back_populates='products')


# Schemas

class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User
        include_fk = True
        include_relationships = True

class OrderSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Order
        include_fk = True  

class ProductSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Product
        include_fk = True
        include_relationships = True

user_schema = UserSchema()
users_schema = UserSchema(many=True) 

order_schema = OrderSchema()
orders_schema = OrderSchema(many=True)

product_schema = ProductSchema()
products_schema = ProductSchema(many=True)


#========== USER(S) ENDPOINTS ==========#

# CREATE USER
@app.route('/users', methods=['POST'])
def create_user():
    try:
        new_user = user_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400 

    #print(new_user)
    new_user = User(user_name=new_user['user_name'], user_address=new_user['user_address'], user_email=new_user['user_email'])
    db.session.add(new_user)
    db.session.commit()

    return user_schema.jsonify(new_user), 201

# RETRIEVE ALL USERS
@app.route('/users', methods=['GET'])
def get_users():
    query = select(User)
    users = db.session.execute(query).scalars().all() 

    return users_schema.jsonify(users), 200

# RETRIEVE INDIVIDUAL USER
@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error message': f'user id not found'})

    return user_schema.jsonify(user), 200

# UPDATE USER 
@app.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'message': 'User id not found'}), 404
    try:
        user_data = user_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400

    user.user_name = user_data['user_name']
    user.user_email = user_data['user_email']

    db.session.commit()
    return user_schema.jsonify(user), 200

# DELETE USER
@app.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    db.session.get(User, user_id)
    user = db.session.get(User, user_id)

    if not user:
        return jsonify({'message': 'User id not found.'}), 404

    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': f'User {user_id} has been deleted'}), 200



#========== PRODUCT(S) ENDPOINTS ==========#

# CREATE A PRODUCT
@app.route('/products', methods=['POST'])
def create_product():
    try:
        product_data = product_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400

    new_poduct = Product(prod_name=product_data['prod_name'], prod_price=product_data['prod_price'])
    db.session.add(new_poduct)
    db.session.commit()

    return product_schema.jsonify(new_poduct), 201

# RETRIEVE ALL PRODUCTS
@app.route('/products', methods=['GET'])
def get_products():
    query = select(Product)
    products = db.session.execute(query).scalars().all()
    return products_schema.jsonify(products), 200

# RETRIEVE INDIVIDUAL PRODUCT
@app.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = db.session.get(Product, product_id)
    if not product:
        return jsonify({'error message': 'product does not exist'})
    return product_schema.jsonify(product), 200

# UPDATE PRODUCT
@app.route('/products/<int:prod_id>', methods=['PUT'])
def update_product(prod_id):
    product = db.session.get(Product, prod_id)
    if not product:
        return jsonify({'message': 'Product id not found'}), 404
    try:
        product_data = product_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400

    product.prod_name = product_data['prod_name']
    product.prod_price = product_data['prod_price']
    
    db.session.commit()
    return product_schema.jsonify(product), 200

# DELETE INDIVIDUAL PRODUCT
@app.route('/products/<int:prod_id>', methods=['DELETE'])
def delete_product(prod_id):
    db.session.get(Product, prod_id)
    product = db.session.get(Product, prod_id)

    if not product:
        return jsonify({'message': 'Product id not found'}), 404
    
    db.session.delete(product)
    db.session.commit()
    return jsonify({'message': f'Product {prod_id} has been deleted'}), 200



#========== ORDER ENDPOINTS =========#

# CREATE A NEW ORDER
@app.route('/orders', methods=['POST'])
def create_order():
    try:
        order_data = order_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400 
    
    new_order = Order(user_id=order_data['user_id'], order_date=order_data['order_date'])
    db.session.add(new_order)
    db.session.commit()

    return order_schema.jsonify(new_order), 201 

# ADD PRODUCT TO AN ORDER
@app.route('/orders/<int:order_id>/add_product/<int:prod_id>', methods=['POST'])
def product_order(order_id, prod_id):
    order = db.session.get(Order, order_id)
    product = db.session.get(Product, prod_id)

    if not order or not product:
        return jsonify({'message': 'Order or Product not found'}), 404

    if product in order.products:
        return jsonify({'message': f'Product {product.prod_id} already exists in order {order.order_id}.'})

    order.products.append(product)
    db.session.commit()
    return jsonify({"message": f"Product {product.prod_id} ({product.prod_name}) has been added to order {order.order_id}"}), 200

# REMOVE PRODUCT FROM ORDER
@app.route('/orders/<int:order_id>/remove_product/<int:prod_id>', methods=['DELETE'])
def product_removal_from_order(prod_id, order_id):
    order = db.session.get(Order, order_id)
    product = db.session.get(Product, prod_id)

    if not order or not product:
        return jsonify({'message': 'Order or Product not found.'}), 404

    if product not in order.products:
        return jsonify({'message': f'Product id {prod_id} not found in order {order_id}.'}), 404

    order.products.remove(product)
    db.session.commit()
    return jsonify({'message': f'Product {product.prod_id} has been removed from Order {order.order_id}.'}), 200

# GET ORDERS FOR USER
@app.route('/orders/users/<int:user_id>', methods=['GET'])
def get_orders(user_id):
    user = db.session.get(User, user_id)
    return orders_schema.jsonify(user.orders), 200

# GET PRODUCTS FOR AN ORDER
@app.route('/orders/<int:order_id>/products', methods=['GET'])
def products_from_order(order_id):
    order = db.session.get(Order, order_id)
    print(f'\nPRINTING:\n', order)
    if not order:
        return jsonify({'message': 'Order not found'}), 404
    
    return products_schema.jsonify(order.products), 200 

if __name__ == '__main__':
    with app.app_context():
        #db.drop_all()
        db.create_all()

    app.run(debug=True)
