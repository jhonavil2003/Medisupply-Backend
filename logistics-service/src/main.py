import os
from flask import Flask
from src.session import db, init_db
from src.blueprints.inventory import inventory_bp
from src.errors.errors import register_error_handlers

def create_app(config=None):
    app = Flask(__name__)
    
    if config:
        app.config.update(config)
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
            'DATABASE_URL',
            'sqlite:///instance/logistics.db'
        )
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'pool_pre_ping': True,
            'pool_recycle': 300,
        }
    
    init_db(app)
    
    app.register_blueprint(inventory_bp)
    
    register_error_handlers(app)
    
    @app.route('/health', methods=['GET'])
    def health():
        return {'status': 'healthy', 'service': 'logistics-service'}, 200
    
    return app

if __name__ == '__main__':
    app = create_app()
    
    port = int(os.getenv('PORT', 3002))
    host = os.getenv('HOST', '0.0.0.0')
    
    app.run(host=host, port=port, debug=True)
