import os
from flask import Flask
from src.session import db, init_db
from src.blueprints.inventory import inventory_bp
from src.blueprints.websocket import websocket_bp
from src.websockets.websocket_manager import init_socketio
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
    
    # Registrar blueprints
    app.register_blueprint(inventory_bp)
    app.register_blueprint(websocket_bp)
    
    # Inicializar WebSocket
    socketio = init_socketio(app)
    
    register_error_handlers(app)
    
    @app.route('/health', methods=['GET'])
    def health():
        return {'status': 'healthy', 'service': 'logistics-service', 'websocket': 'enabled'}, 200
    
    return app, socketio

if __name__ == '__main__':
    app, socketio = create_app()
    
    port = int(os.getenv('PORT', 3002))
    host = os.getenv('HOST', '0.0.0.0')
    
    # Usar socketio.run en lugar de app.run para soportar WebSockets
    socketio.run(app, host=host, port=port, debug=True, allow_unsafe_werkzeug=True)
