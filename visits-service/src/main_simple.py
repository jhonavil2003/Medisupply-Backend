import os
from flask import Flask, jsonify
from src.session import db, init_db
from src.blueprints.visits import visits_bp


def create_app(config=None):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Default configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
        'DATABASE_URL',
        'postgresql://visitsuser:visits_secure_password_2024@localhost:5435/visits_db'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    if config:
        app.config.update(config)
    
    db.init_app(app)
    
    # Importar modelos para que SQLAlchemy los reconozca
    from src.entities import Salesperson, Visit, VisitFile, VisitStatus
    
    app.register_blueprint(visits_bp)
    
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