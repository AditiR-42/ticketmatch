import os

class Config:
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABSE_URL')