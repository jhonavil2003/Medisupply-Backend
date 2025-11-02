from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Session es un alias para db.session para compatibilidad
Session = db.session

def init_db(app):
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
