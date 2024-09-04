from flask import Flask, request, jsonify
from flask_migrate import Migrate
from dotenv import load_dotenv
import psycopg2
from app.models import *
import os
from config import config
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_login import LoginManager, login_user, logout_user, current_user


load_dotenv()

app = Flask(__name__)
config_name = os.getenv("FLASK_CONFIG", "default")
app.config.from_object(config[config_name])

db.init_app(app)
migrate = Migrate(app, db)
jwt = JWTManager(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.session_protection = 'strong'
login_manager.login_view = 'login'

#initializing the database
with app.app_context():
    db.create_all()
    
@app.route('/signup/grocer', methods=['POST'])
def create_grocer():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    phone_number = data.get('phone_number')
    stall_name = data.get('stall_name')
    stall_number = data.get('stall_number')
    password = data.get('password')
    
    if Grocer.query.filter((Grocer.email == email) | (Grocer.phone_number == phone_number)).first():
        return jsonify({"error": "Email or phone number exists"}), 400
    
    new_grocer = Grocer(name=name, email=email, phone_number=phone_number, stall_name=stall_name, stall_number=stall_number)
    new_grocer.hash_password(password)
    db.session.add(new_grocer)
    db.session.commit()
    
    return jsonify({"Grocer Registration Succesful"}), 201

@app.route('/signup/farmer', methods=['POST'])
def create_farmer():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    phone_number = data.get('phone_number')
    password = data.get('password')
    
    if Farmer.query.filter((Farmer.email == email) | (Farmer.phone_number == phone_number)).first():
        return jsonify({"Error": "Email or Phone Number exists"}), 400
    
    new_farmer = Farmer(name=name, email=email,phone_number=phone_number)
    new_farmer.hash_password(password)
    db.session.add(new_farmer)
    db.session.commit()
    
    return jsonify({"Farmer Registration Successful"}), 201

@app.route('/login/grocer', methods=['POST'])
def login_grocer():
    data = request.get_json()
    identifier = data.get('identifier')
    password = data.get('password')
    
    grocer = Grocer.query.filter((Grocer.email == identifier) | (Grocer.phone_number == identifier)).first()
    
    if grocer and grocer.check_password(password):
        login_user(grocer)
        access_token = create_access_token(identity=grocer.id)
        return jsonify(access_token=access_token), 200
    else:
        return jsonify({"error": "That's not correct sorry"}), 401
    
@app.route('/login/farmer', methods=['POST'])
def login_farmer():
    data = request.get_json()
    identifier = data.get('identifier')
    password = data.get('identifier')
    
    farmer = Farmer.query.filter((Farmer.email == identifier) | (Farmer.phone_number == identifier)).first()
    
    if farmer and farmer.check_password(password):
        login_user(farmer)
        access_token = create_access_token(identity=farmer.id)
        return jsonify(access_token=access_token), 200
    else:
        return jsonify({"error": "Yeah something's not quite right try again"}), 401
    
@app.route('/products', methods=['GET'])
@jwt_required
def view_products():
    current_user.id = get_jwt_identity()
    products = Product.query.all()
    return jsonify([product.to_dict() for product in products]), 200

@app.route('/products/create', methods=['POST'])
@jwt_required
def create_products():
    current_user.id = get_jwt_identity()
    data = request.get_json()
    name = data.get('name')
    price = data.get('price')
    farmer_name = current_user.name
    
    new_product = Product(name=name, price=price, farmer_name=farmer_name)
    db.session.add(new_product)
    db.session.commit()
    
    return jsonify("Product added"), 201

@app.route('/orders/create', methods=['POST'])
@jwt_required()
def create_order():
    current_user.id = get_jwt_identity()
    data = request.get_json()
    grocer_id = data.get('grocer_id')
    product_ids = data.get('product_ids')
    
    grocer = Grocer.query.get(grocer_id)
    if not grocer:
        return jsonify({"Error": "Grocer not found"}), 400
    
    products = Product.query.filter(Product.id.in_(product_ids)).all()
    if not products:
        return jsonify({"Error": "products not found"}), 401
    
    new_order = Order(grocer_id=grocer.id, products=products)
    db.session.add(new_order)
    db.session.commit()
    
    return jsonify({"Message": "Order created successfully"}), 201

@app.route('/orders', methods=['GET'])
@jwt_required()
def get_farmerOrders():
    current_user = get_jwt_identity()
    farmer_id = current_user['id']
    
    orders = Order.query.join(order_product).join(Product).filter(Product.farmer_id == farmer_id).all()
    order_list = []
    for order in orders:
        order_details = {
            "order_id": order.id,
            "grocer_name": order.grocer.name,
            "products": [{"name": product.name, "price": product.price} for product in order.products],
            "quantity": order.quantity,
            "created_at": order.created_at
        }
        order_list.append(order_details)
        
    return jsonify({"farmer_id": farmer_id, "orders": order_list}), 200

@app.route('/my_orders', methods=['GET'])
@jwt_required
def get_grocerOrders():
    current_user = get_jwt_identity()
    grocer_id = current_user['id']
    
    orders = Order.query.filter_by(grocer_id=grocer_id).all()
    order_list = []
    for order in orders:
        order_details = {
            "order_id": order.id,
            "products": [
                {
                "name": product.name,
                "price": product.price,
                "farmer": product.farmer.name
                } for product in order.products
            ],
            "quantity": order.quantity,
            "created_at": order.created_at
        }
        order_list.append(order_details)
        
    return jsonify({"grocer_id": grocer_id, "orders": order_list}), 200





if __name__ == '__main__':
    app.run(port=5000, debug=True)