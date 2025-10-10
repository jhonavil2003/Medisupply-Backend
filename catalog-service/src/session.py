from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os

load_dotenv()

db = SQLAlchemy()

def init_db(app):
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
