import os
from flask import Flask, jsonify
from flask_cors import CORS
from src.session import db, init_db
from src.errors.errors import register_error_handlers
from src.blueprints.customers import customers_bp
from src.blueprints.orders import orders_bp
from src.blueprints.visits import visits_bp
from src.blueprints.salespersons import salespersons_bp
from src.blueprints.visit_files import visit_files_bp, files_bp
from src.blueprints.salesperson_goals import salesperson_goals_bp


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
    # Configuration for file uploads
    app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB
    
    if config:
        app.config.update(config)
        if 'sqlite' in app.config.get('SQLALCHEMY_DATABASE_URI', ''):
            app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {}
    
    init_db(app)
    
    # Configurar CORS para permitir conexiones desde aplicación Android
    CORS(app, resources={
        r"/api/*": {
            "origins": ["*"],  # En producción, especificar dominios específicos
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"]
        }
    })
    
    register_error_handlers(app)
    
    app.register_blueprint(customers_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(visits_bp)
    app.register_blueprint(salespersons_bp)
    app.register_blueprint(visit_files_bp)
    app.register_blueprint(files_bp)  # Blueprint global para DELETE /api/visits/files/{fileId}
    app.register_blueprint(salesperson_goals_bp)  # Blueprint para objetivos de vendedores
    
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
