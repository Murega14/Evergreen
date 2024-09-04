import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv()

class Config:
    """Base Configuration"""
    SECRET_KEY = os.getenv('SECRET_KEY')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
    JWT_TOKEN_LOCATION = ['headers']
    

@staticmethod
def init_app(app):
    pass

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI')

#class TestingConfig(Config):
    #DEBUG = True
    #TESTING = True
    #SQLALCHEMY_DATABASE_URI = []

#class ProductionConfig(Config):
    #DEBUG = False
    #SQLALCHEMY_DATABASE_URI = []

config = {
    'development': DevelopmentConfig,
    'default': DevelopmentConfig
}