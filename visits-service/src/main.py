import os
from flask import Flask, jsonify
from src.session import db, init_db
from src.errors.errors import register_error_handlers
# from src.blueprints.visits import visits_bp  # Comentado temporalmente por errores de import
from src.blueprints.visit_files import visit_files_bp


def create_app(config=None):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Default configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
        'DATABASE_URL',
        'postgresql://visitsuser:visits_secure_password_2024@localhost:5435/visits_db'
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
    
    register_error_handlers(app)
    
    # app.register_blueprint(visits_bp)  # Comentado temporalmente
    app.register_blueprint(visit_files_bp)
    
    @app.route('/health', methods=['GET'])
    def health():
        return jsonify({
            'service': 'visits-service',
            'status': 'healthy',
            'version': '1.0.0'
        }), 200
    
    return app


if __name__ == '__main__':
    app = create_app()
    port = int(os.getenv('SERVICE_PORT', 3004))
    app.run(host='0.0.0.0', port=port, debug=True)