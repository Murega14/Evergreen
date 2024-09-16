from flask import Flask, request, jsonify
from flask_migrate import Migrate
from dotenv import load_dotenv
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

#db.configure_mappers()

#initializing the database
with app.app_context():
    db.create_all()
    
@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    phone_number = data.get('phone_number')
    password = data.get('password')
    role = data.get('role')
    
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
        login_user(user)
        access_token = create_access_token(identity=user.id)
        session_token = str(access_token)
        newSession = LoginSession(user_id=user.id, session_token=session_token)
        db.session.add(newSession)
        db.commit()
        
        return jsonify(access_token=access_token), 200
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
        
        return jsonify(productList)
    
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
        

if __name__ == '__main__':
    app.run(port=5000, debug=True)
