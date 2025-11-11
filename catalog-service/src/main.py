import os
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

from src.session import db, init_db
from src.errors.errors import register_error_handlers
from src.blueprints.products import products_bp
from src.blueprints.suppliers import suppliers_bp

load_dotenv()

def create_app(config=None):
    app = Flask(__name__)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/catalog_db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JSON_SORT_KEYS'] = False
    
    if config:
        app.config.update(config)
    
    CORS(app)
    db.init_app(app)
    
    register_error_handlers(app)
    
    app.register_blueprint(products_bp)
    app.register_blueprint(suppliers_bp)
    
    @app.route('/', methods=['GET'])
    def index():
        return jsonify({
            'service': 'MediSupply Catalog Service',
            'version': '1.0.0',
            'status': 'running',
            'endpoints': {
                'products': '/products',
                'suppliers': '/suppliers',
                'health': '/health'
            }
        }), 200
    
    @app.route('/health', methods=['GET'])
    def health_check():
        return jsonify({
            'status': 'healthy',
            'service': 'catalog-service',
            'database': 'connected' if db.engine else 'disconnected'
        }), 200
    
    with app.app_context():
        db.create_all()
    
    return app


def main():
    app = create_app()
    
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 3001))
    debug = os.getenv('FLASK_ENV', 'development') == 'development'
        
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    main()
