"""
Configuración centralizada del Video Service
============================================

Gestiona variables de entorno y configuración del sistema.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()


class Config:
    """Configuración centralizada del servicio"""
    
    # ========== SERVICIO ==========
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    SERVICE_PORT = int(os.getenv('SERVICE_PORT', 3004))
    HOST = os.getenv('HOST', '0.0.0.0')
    DEBUG = FLASK_ENV == 'development'
    
    # ========== GOOGLE AI ==========
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
    
    if not GOOGLE_API_KEY:
        raise ValueError(
            "GOOGLE_API_KEY not found in environment variables. "
            "Please set it in .env file or system environment."
        )
    
    # ========== MCP CONFIGURATION ==========
    RAG_MCP_SERVER_PATH = os.getenv(
        'RAG_MCP_SERVER_PATH',
        '/app/mcp_server/rag_server.py'
    )
    
    # URL del RAG Backend (usado por el servidor MCP)
    RAG_API_URL = os.getenv(
        'RAG_API_URL',
        'http://host.docker.internal:8001/api/v1/ask'
    )
    
    # ========== VIDEO PROCESSING ==========
    MAX_FRAMES_PER_VIDEO = int(os.getenv('MAX_FRAMES_PER_VIDEO', 10))
    FRAME_EXTRACTION_INTERVAL = int(os.getenv('FRAME_EXTRACTION_INTERVAL', 5))
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads/frames')
    MAX_VIDEO_SIZE_MB = int(os.getenv('MAX_VIDEO_SIZE_MB', 50))
    MAX_CONTENT_LENGTH = MAX_VIDEO_SIZE_MB * 1024 * 1024  # Convertir a bytes
    VIDEO_DOWNLOAD_TIMEOUT = int(os.getenv('VIDEO_DOWNLOAD_TIMEOUT', 120))
    
    # ========== GEMINI VISION ==========
    GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.0-flash-exp')
    GEMINI_TEMPERATURE = float(os.getenv('GEMINI_TEMPERATURE', 0.3))
    GEMINI_MAX_TOKENS = int(os.getenv('GEMINI_MAX_TOKENS', 2048))
    
    # ========== AWS S3 ==========
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
    AWS_BUCKET_NAME = os.getenv('AWS_BUCKET_NAME')
    
    # ========== LOGGING ==========
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # ========== PATHS ==========
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    UPLOAD_DIR = BASE_DIR / UPLOAD_FOLDER
    
    @classmethod
    def ensure_directories(cls):
        """Crea directorios necesarios si no existen"""
        cls.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        (cls.UPLOAD_DIR / 'frames').mkdir(exist_ok=True)
    
    @classmethod
    def validate(cls):
        """Valida que la configuración sea correcta"""
        errors = []
        
        if not cls.GOOGLE_API_KEY:
            errors.append("GOOGLE_API_KEY is required")
        
        if cls.MAX_FRAMES_PER_VIDEO < 1:
            errors.append("MAX_FRAMES_PER_VIDEO must be >= 1")
        
        if cls.GEMINI_TEMPERATURE < 0 or cls.GEMINI_TEMPERATURE > 1:
            errors.append("GEMINI_TEMPERATURE must be between 0 and 1")
        
        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")
        
        return True
    
    @classmethod
    def to_dict(cls):
        """Convierte configuración a diccionario (sin exponer secrets)"""
        return {
            'service': {
                'env': cls.FLASK_ENV,
                'port': cls.SERVICE_PORT,
                'host': cls.HOST,
                'debug': cls.DEBUG,
            },
            'video': {
                'max_frames': cls.MAX_FRAMES_PER_VIDEO,
                'frame_interval': cls.FRAME_EXTRACTION_INTERVAL,
                'max_size_mb': cls.MAX_VIDEO_SIZE_MB,
            },
            'gemini': {
                'model': cls.GEMINI_MODEL,
                'temperature': cls.GEMINI_TEMPERATURE,
                'max_tokens': cls.GEMINI_MAX_TOKENS,
            },
            'mcp': {
                'server_path': cls.RAG_MCP_SERVER_PATH,
                'rag_url': cls.RAG_API_URL,
            }
        }


# Inicializar y validar configuración al importar
Config.validate()
Config.ensure_directories()
