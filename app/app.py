from flask import Flask, request, jsonify, make_response
from flask_migrate import Migrate
from dotenv import load_dotenv
from app.models import *
import os
from app.config import config
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from datetime import timedelta

load_dotenv()

app = Flask(__name__)
config_name = os.getenv("FLASK_CONFIG", "prod")
app.config.from_object(config[config_name])

db.init_app(app)
migrate = Migrate(app, db)
jwt = JWTManager(app)


#db.configure_mappers()

#initializing the database
with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return f"welcome to Evergreen"
    
@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    phone_number = data.get('phone_number')
    password = data.get('password')
    role = data.get('role')
    
    if not all(name, email, phone_number, password, role):
        return jsonify({"error": "all fields are required"})
    
    if User.query.filter((User.email == email) | (User.phone_number == phone_number)).first():
        return jsonify({"error": "two legends cannot coexist sorry, the email or phonenumber exists"}), 400 
    
    newUser = User(name=name, email=email, phone_number=phone_number, role=role)
    newUser.hash_password(password)
    db.session.add(newUser)
    db.session.commit()

    if role == 'farmer':
        newFarmer = Farmer(user_id=newUser.id)
        db.session.add(newFarmer)
    elif role == 'grocer':
        newGrocer = Grocer(user_id=newUser.id, store_name=data.get('store_name'))
        db.session.add(newGrocer)

    db.session.commit()
    
    return({"message": "user created successfully hooray"}), 201
    
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    identifier = data.get('identifier')
    password = data.get('password')
    
    user = User.query.filter((User.email == identifier) | (User.phone_number == identifier)).first()
    if user and user.check_password(password):
        expires = timedelta(hours=1)
        access_token = create_access_token(identity=user.id, expires_delta=expires)
        
        response = make_response(jsonify({"login": "success"}))
        response.set_cookie("session_token",
                            access_token,
                            httponly=True,
                            secure=True)
        
        return jsonify(response), 200
    else:
        return jsonify({"error": "we've got an imposter"}), 401

@app.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    user_id = get_jwt_identity()
    session_token = request.headers.get('session_token') or request.json.get('session_token')
    session = LoginSession.query.filter_by(user_id=user_id, session_token=session_token, logout_time=None).first()
    
    if session:
        session.logout_time = db.func.current_timestamp()
        db.session.commit()
        
        return jsonify({"message": "Logout successful, session terminated"}), 200
    else:
        return jsonify({"error": "No active session found"}), 400
    
@app.route('/products', methods=['GET', 'POST'])
@jwt_required()
def products():
    userId = get_jwt_identity()
    if request.method == 'GET':
        products = Product.query.all()
        productList = []
        
        for product in products:
            farmersName = product.farmer.user.name
            productDetails = {
                "name": product.name,
                "description": product.description,
                "quantity": product.quantity_available,
                "price": product.price_per_unit,
                "farmer": farmersName
            }
            productList.append(productDetails)
        
        return jsonify(productList), 200
    
    if request.method == 'POST':
        data = request.get_json()
        # Check if the user is a farmer
        farmer = Farmer.query.filter_by(user_id=userId).first()
        
        if not farmer:
            return jsonify({"error": "Only farmers can add products"}), 403
        
        name = data.get('name')
        description = data.get('description')
        quantity_available = data.get('quantity_available')
        price_per_unit = data.get('price_per_unit')
        
        newProduct = Product(farmer_id=farmer.id, name=name, description=description,
                             quantity_available=quantity_available, price_per_unit=price_per_unit)
        db.session.add(newProduct)
        db.session.commit()
        
        return jsonify({"message": "product created"}), 201
    
@app.route('/orders', methods=['GET', 'POST'])
@jwt_required()
def orders():
    userId = get_jwt_identity()
    user = User.query.get(userId)
    
    if request.method == 'GET':
        if user.role == 'farmer':
            return getFarmerOrders(user)
        elif user.role == 'grocer':
            return getGrocerOrders(user)
        else:
            return jsonify({"error": "Invalid. Unauthorized access"}), 403
    
    if request.method == 'POST':
        data = request.get_json()
        orderItems = data.get('order_items')
        
        if not orderItems:
            return jsonify({"error": "no items in the order oops"}), 400
        
        totalAmount = 0
        orderItemList = []
        
        for item in orderItems:
            product_id = item.get('product_id')
            quantity_ordered = item.get('quantity')
            
            product = Product.query.filter_by(id=product_id).first()
            
            if not product:
                return jsonify({"error": "product not found"}), 400
            
            if product.quantity_available < quantity_ordered:
                return jsonify({"error": f"we don't have that much sorry, there's only {product.quantity_available}"})
            
            totalPrice = product.price_per_unit * quantity_ordered
            totalAmount += totalPrice
            
            orderItem = OrderItem(
                product_id=product.id,
                quantity_ordered=quantity_ordered,
                price_per_unit=product.price_per_unit,
                total_price=totalPrice
            )
            orderItemList.append(orderItem)
            
            product.quantity_available -= quantity_ordered
            
        newOrder = Order(grocer_id=userId, total_amount=totalAmount)
        db.session.add(newOrder)
        db.session.flush()
        
        for orderItem in orderItemList:
            orderItem.order_id = newOrder.id
            db.session.add(orderItem)
            
        db.session.commit()
        
        return jsonify({"message": "order created"}), 201

def getFarmerOrders(user):
    farmer = Farmer.query.filter_by(user_id=user.id).first()
    if not farmer:
        return jsonify({"message": "farmer profile not found"}), 404
    
    orders = Order.query.join(OrderItem).join(Product).filter(Product.farmer_id == farmer.id).distinct().all()
    
    orderList = []
    for order in orders:
        productList = []
        
        for item in order.items:
            if item.product.farmer_id == farmer.id:
                productDetails = {
                    "product_name": item.product.name,
                    "quantity_ordered": item.quantity_ordered,
                    "price_per_unit": item.price_per_unit
                }
                productList.append(productDetails)
                
        totalAmount = sum(item.total_price for item in order.items if item.product.farmer_id == farmer.id)
            
        grocerName = order.grocer.user.name if order.grocer and order.grocer.user else "Unknown"
        orderDetails = {
            "order_id": order.id,
            "grocer_name": grocerName,
            "products": productList,
            "total_amount": totalAmount,
            "order_date": order.order_date
        }
        orderList.append(orderDetails)
        
            
    return jsonify(orderList), 200

def getGrocerOrders(user):
    grocer = Grocer.query.filter_by(user_id=user.id).first()
    if not grocer:
        return jsonify({"message": "Grocer profile not found"}), 404
    
    orders = Order.query.filter_by(grocer_id=grocer.id).all()
    
    orderList = []
    for order in orders:
        productList = []
        
        for item in order.items:
            grocerName = item.order.grocer.user.name
            productDetails = {
                "product_name": item.product.name,
                "farmer_name": item.product.farmer.user.name,
                "quantity_ordered": item.quantity_ordered,
                "price_per_unit": item.price_per_unit,
                "total_price": item.total_price
            }
            productList.append(productDetails)
        
        orderDetails = {
            "order_id": order.id,
            "grocer_name": grocerName,
            "products": productList,
            "total_amount": order.total_amount,
            "order_date": order.order_date
        }
        orderList.append(orderDetails)
        
    return jsonify(orderList), 200

if __name__ == '__main__':
    app.run(port=5000, debug=True)
