from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import MetaData

metadata = MetaData()

db = SQLAlchemy(metadata=metadata)

#association table
order_product = db.Table('order_product',
                         db.Column('order_id', db.Integer, db.ForeignKey('orders.id'), primary_key=True),
                         db.Column('product_id', db.Integer, db.ForeignKey('products.id'), primary_key=True))


class Grocer(db.Model):
    __tablename__ = 'grocers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(), nullable=False, unique=False)
    phone_number = db.Column(db.String(), unique=True, nullable=False)
    stall_name = db.Column(db.String(), unique=True, nullable=False)
    stall_number = db.Column(db.Integer, unique=True, nullable=False)
    password_hash = db.Column(db.String(), nullable=False)
    orders = db.relationship('Order', back_populates='grocer', lazy=True, cascade="all, delete-orphan")
    
    def hash_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f"<Grocer {self.name}, {self.phone_number}, {self.stall_name}, {self.stall_number}>"
    
class Farmer(db.Model):
    __tablename__ = 'farmers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    phone_number = db.Column(db.String(), nullable=False, unique=True)
    email = db.Column(db.String(), nullable=False, unique=True)
    password_hash = db.Column(db.String(), nullable=False)
    
    def hash_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
        
    def __repr__(self):
        return f"<Farmer {self.name}, {self.phone_number}>"
    
class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), nullable=False, index=True)
    price = db.Column(db.Integer, nullable=False)
    farmer_id = db.Column(db.Integer, db.ForeignKey('farmers.id'), nullable=False)
    farmer = db.relationship('Farmer', backref=db.backref('products', lazy=True))
    
    def __repr__(self):
        return f"<Product {self.name}, {self.price}, Farmer: {self.farmer_id}>"
    
class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    products = db.relationship('Product', secondary=order_product, lazy='subquery', backref=db.backref('orders', lazy=True))
    quantity = db.Column(db.Integer, nullable=False)
    grocer_id = db.Column(db.Integer, db.ForeignKey('grocers.id'), nullable=False)

    grocer = db.relationship('Grocer', back_populates='orders')

    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    def __repr__(self):
        return f"<Order ID: {self.id}, Grocer ID: {self.grocer_id}, Quantity: {self.quantity}>"
