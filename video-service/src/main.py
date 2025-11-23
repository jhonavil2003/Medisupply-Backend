"""Video Service - Análisis de videos con IA para MediSupply."""

import os
import sys
import logging
from flask import Flask
from flask_cors import CORS

from src.utils.config import Config
from src.errors.errors import register_error_handlers
from src.blueprints.video_analysis import video_analysis_bp
from src.blueprints.health import health_bp

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def create_app(config_object=None):
    """Crea y configura la aplicación Flask."""
    app = Flask(__name__)
    
    logger.info("=" * 70)
    logger.info("🚀 Initializing Video Service")
    logger.info("=" * 70)
    
    # ===== CARGAR CONFIGURACIÓN =====
    if config_object:
        app.config.from_object(config_object)
    else:
        # Usar configuración desde variables de entorno
        app.config['GOOGLE_API_KEY'] = Config.GOOGLE_API_KEY
        app.config['GEMINI_MODEL'] = Config.GEMINI_MODEL
        app.config['RAG_API_URL'] = Config.RAG_API_URL
        app.config['MAX_FRAMES'] = Config.MAX_FRAMES_PER_VIDEO
    
    try:
        Config.validate()
        logger.info("✅ Configuration validated successfully")
    except ValueError as e:
        logger.error(f"❌ Configuration validation failed: {e}")
        sys.exit(1)
    
    try:
        Config.ensure_directories()
        logger.info("✅ Required directories created/verified")
    except Exception as e:
        logger.warning(f"⚠️ Directory creation warning: {e}")
    
    # Configurar CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": "*",
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    logger.info("✅ CORS configured")
    
    app.register_blueprint(health_bp)
    logger.info("✅ Health Blueprint registered")
    
    app.register_blueprint(video_analysis_bp)
    logger.info("✅ Video Analysis Blueprint registered")
    
    register_error_handlers(app)
    logger.info("✅ Error handlers registered")
    
    logger.info("\n📋 Service Configuration:")
    logger.info(f"   - Gemini Model: {Config.GEMINI_MODEL}")
    logger.info(f"   - Max Frames: {Config.MAX_FRAMES_PER_VIDEO}")
    logger.info(f"   - RAG API: {Config.RAG_API_URL or 'Not configured'}")
    logger.info(f"   - Upload Dir: {Config.UPLOAD_FOLDER}")
    logger.info(f"   - Environment: {os.getenv('FLASK_ENV', 'production')}")
    
    # ===== RUTA RAÍZ =====
    @app.route('/')
    def index():
        """Endpoint raíz con información del servicio"""
        return {
            'service': 'Video Analysis Service',
            'version': '1.0.0',
            'status': 'running',
            'endpoints': {
                'health': '/health',
                'analyze': '/api/videos/analyze',
                'formats': '/api/videos/supported-formats'
            },
            'documentation': 'https://github.com/MediSupply/video-service'
        }
    
    logger.info("=" * 70)
    logger.info("✅ Video Service initialized successfully")
    logger.info("=" * 70)
    
    return app


# ===== ENTRY POINT =====
if __name__ == '__main__':
    """
    Entry point para desarrollo local.
    
    En producción, usar Gunicorn o uWSGI:
        gunicorn -w 4 -k uvicorn.workers.UvicornWorker src.main:app
    """
    # Crear aplicación
    app = create_app()
    
    # Obtener configuración de host/port
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 3004))
    debug = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    
    logger.info(f"\n🌐 Starting server on {host}:{port}")
    logger.info(f"   Debug mode: {debug}")
    logger.info(f"   Access at: http://{host}:{port}")
    logger.info(f"   Health check: http://{host}:{port}/health")
    logger.info(f"   API endpoint: http://{host}:{port}/api/videos/analyze\n")
    
    # Ejecutar servidor
    try:
        # IMPORTANTE: Flask 3.0 con async routes requiere un servidor ASGI
        # Para desarrollo, usamos el servidor built-in de Flask
        # Para producción, usar Gunicorn con Uvicorn workers
        
        from asgiref.wsgi import WsgiToAsgi
        import uvicorn
        
        # Convertir WSGI app a ASGI
        asgi_app = WsgiToAsgi(app)
        
        # Ejecutar con Uvicorn
        uvicorn.run(
            asgi_app,
            host=host,
            port=port,
            log_level="info" if not debug else "debug"
        )
        
    except ImportError:
        # Fallback: usar servidor Flask built-in (solo desarrollo)
        logger.warning(
            "⚠️ uvicorn/asgiref not available. "
            "Using Flask built-in server (not recommended for async routes)"
        )
        app.run(
            host=host,
            port=port,
            debug=debug,
            threaded=True
        )
    
    except KeyboardInterrupt:
        logger.info("\n\n👋 Server stopped by user")
    
    except Exception as e:
        logger.error(f"\n❌ Server error: {str(e)}", exc_info=True)
        sys.exit(1)
