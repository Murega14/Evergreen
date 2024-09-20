from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import MetaData

metadata = MetaData()

db = SQLAlchemy(metadata=metadata)

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True)
    phone_number = db.Column(db.String(12), nullable=False, unique=True)
    password_hash = db.Column(db.String(120), nullable=False)
    role = db.Column(db.Enum("farmer", "grocer"), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    farmer = db.relationship('Farmer', backref='user', uselist=False)
    grocer = db.relationship('Grocer', backref='user', uselist=False)
    login_sessions = db.relationship('LoginSession', backref='user', lazy=True)
    
    def hash_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @property
    def is_active(self):
        return True
    
    @property
    def is_authenticated(self):
        return True
    
    def get_id(self):
        return str(self.id)
    
    def __repr__(self):
        return f"<User: {self.id}, {self.name}, {self.email}, {self.phone_number}, {self.role}>"
    
class Farmer(db.Model):
    __tablename__ = 'farmers'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    products = db.relationship('Product', backref='farmer', lazy=True)
    
    def __repr__(self):
        return f"<Farmer: {self.id}, {self.user_id}>"

class Grocer(db.Model):
    __tablename__ = 'grocers'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    store_name = db.Column(db.String(120), nullable=False, unique=True)
    
    orders = db.relationship('Order', backref='grocer', lazy=True)

    def __repr__(self):
        return f"<Grocer: {self.id}, {self.user_id}, {self.store_name}>"
    
class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    farmer_id = db.Column(db.Integer, db.ForeignKey('farmers.id'))
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(400))
    quantity_available = db.Column(db.Integer, nullable=False)
    price_per_unit = db.Column(db.Integer, nullable=False)
    
    order_items = db.relationship('OrderItem', backref='product', lazy=True)
    
    def __repr__(self):
        return f"<Product {self.id}, {self.farmer_id}, {self.name}, {self.description}, {self.quantity_available}, {self.price_per_unit}>"
    
class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    grocer_id = db.Column(db.Integer, db.ForeignKey('grocers.id'))
    total_amount = db.Column(db.Integer, nullable=False)
    order_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    delivery_date = db.Column(db.DateTime, default=None)
    
    items = db.relationship('OrderItem', backref='order', lazy=True)
    
    def __repr__(self):
        return f"<Order: {self.id}, {self.grocer_id}, {self.total_amount}, {self.order_date}, {self.delivery_date}>"
    
class OrderItem(db.Model):
    __tablename__ = 'orderItems'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    quantity_ordered = db.Column(db.Integer, nullable=False)
    price_per_unit = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Integer, nullable=False)
    
    def __repr__(self):
        return f"<OrderItem: {self.order_id}, {self.product_id}, {self.quantity_ordered}, {self.price_per_unit}, {self.total_price}>"
    
class LoginSession(db.Model):
    __tablename__ = 'loginSession'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    session_token = db.Column(db.String(120), nullable=False)
    login_time = db.Column(db.DateTime, default=db.func.current_timestamp())
    logout_time = db.Column(db.DateTime, default=None)
    
    def __repr__(self):
        return f"<LoginSession: {self.id}, {self.user_id}, {self.session_token}, {self.login_time}, {self.logout_time}>"