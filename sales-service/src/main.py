import os
from flask import Flask, jsonify
from src.session import db, init_db
from src.errors.errors import register_error_handlers
from src.blueprints.customers import customers_bp
from src.blueprints.orders import orders_bp


def create_app(config=None):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Default configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
        'DATABASE_URL',
        'postgresql://salesuser:salespass@localhost:5434/sales_db'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True
    }
    
    if config:
        app.config.update(config)
        if 'sqlite' in app.config.get('SQLALCHEMY_DATABASE_URI', ''):
            app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {}
    
    init_db(app)
    
    register_error_handlers(app)
    
    app.register_blueprint(customers_bp)
    app.register_blueprint(orders_bp)
    
    @app.route('/health', methods=['GET'])
    def health():
        return jsonify({
            'service': 'sales-service',
            'status': 'healthy',
            'version': '1.0.0'
        }), 200
    
    return app


if __name__ == '__main__':
    app = create_app()
    port = int(os.getenv('SERVICE_PORT', 3003))
    app.run(host='0.0.0.0', port=port, debug=True)
