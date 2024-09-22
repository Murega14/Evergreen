import pytest
from app.app import app, db
from app.models import User, Farmer, Grocer, Product, Order, OrderItem
from flask_jwt_extended import create_access_token

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    client = app.test_client()

    with app.app_context():
        db.create_all()

    yield client

    with app.app_context():
        db.drop_all()

@pytest.fixture
def auth_headers(client):
    with app.app_context():
        user = User(name="Test User", email="test@example.com", phone_number="1234567890", role="farmer")
        user.hash_password("password123")
        db.session.add(user)
        db.session.commit()
        access_token = create_access_token(identity=user.id)
    
    return {'Authorization': f'Bearer {access_token}'}

def test_signup(client):
    response = client.post('/signup', json={
        "name": "John Doe",
        "email": "john@example.com",
        "phone_number": "1234567890",
        "password": "secret",
        "role": "farmer"
    })
    assert response.status_code == 201
    assert b"user created successfully" in response.data

def test_login(client):
    # First, create a user
    client.post('/signup', json={
        "name": "Jane Doe",
        "email": "jane@example.com",
        "phone_number": "0987654321",
        "password": "secret",
        "role": "grocer",
        "store_name": "Jane's Grocery"
    })

    # Now, try to login
    response = client.post('/login', json={
        "identifier": "jane@example.com",
        "password": "secret"
    })
    assert response.status_code == 200
    assert 'access_token' in response.json

def test_logout(client, auth_headers):
    response = client.post('/logout', headers=auth_headers, content_type='application/json')
    assert response.status_code == 200
    assert b"Logout successful" in response.data

def test_get_products(client, auth_headers):
    response = client.get('/products', headers=auth_headers, content_type='application/json')
    assert response.status_code == 200
    assert isinstance(response.json, list)

def test_create_product(client, auth_headers):
    response = client.post('/products', headers=auth_headers, json={
        "name": "Apple",
        "description": "Fresh red apples",
        "quantity_available": 100,
        "price_per_unit": 0.5
    })
    assert response.status_code == 201
    assert b"product created" in response.data

def test_get_orders_farmer(client, auth_headers):
    response = client.get('/orders', headers=auth_headers, content_type='application/json')
    assert response.status_code == 200
    assert isinstance(response.json, list)

def test_create_order(client, auth_headers):
    # First, create a product
    client.post('/products', headers=auth_headers, json={
        "name": "Banana",
        "description": "Fresh yellow bananas",
        "quantity_available": 100,
        "price_per_unit": 0.3
    })

    # Now, create an order
    response = client.post('/orders', headers=auth_headers, json={
        "order_items": [
            {
                "product_id": 1,
                "quantity": 10
            }
        ]
    })
    assert response.status_code == 201
    assert b"order created" in response.data

def test_get_orders_grocer(client):
    # Create a grocer user
    client.post('/signup', json={
        "name": "Grocer Joe",
        "email": "joe@example.com",
        "phone_number": "1122334455",
        "password": "secret",
        "role": "grocer",
        "store_name": "Joe's Store"
    })

    # Login as grocer
    login_response = client.post('/login', json={
        "identifier": "joe@example.com",
        "password": "secret"
    })
    grocer_token = login_response.json['access_token']
    grocer_headers = {'Authorization': f'Bearer {grocer_token}'}

    # Get orders as grocer
    response = client.get('/orders', headers=grocer_headers)
    assert response.status_code == 200
    assert isinstance(response.json, list)

if __name__ == '__main__':
    pytest.main()