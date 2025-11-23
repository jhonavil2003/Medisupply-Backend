from flask import Blueprint, jsonify
import logging
import asyncio

from src.utils.config import Config
from src.services.mcp_client_service import get_mcp_client

logger = logging.getLogger(__name__)

# Crear Blueprint
health_bp = Blueprint('health', __name__)


@health_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check básico.
    
    Verifica que el servicio esté vivo y respondiendo.
    
    Response:
    {
        "status": "healthy",
        "service": "video-service",
        "version": "1.0.0"
    }
    
    Status: 200 OK
    """
    return jsonify({
        'status': 'healthy',
        'service': 'video-service',
        'version': '1.0.0',
        'message': 'Video analysis service is running'
    }), 200


@health_bp.route('/health/ready', methods=['GET'])
async def readiness_check():
    """
    Readiness check detallado.
    
    Verifica que el servicio esté listo para recibir tráfico:
    - Configuración válida
    - Conexión con MCP/RAG (opcional)
    - Gemini API configurada
    
    Response:
    {
        "status": "ready",
        "checks": {
            "config": "ok",
            "gemini": "ok",
            "mcp": "ok"
        }
    }
    
    Status:
    - 200: Servicio listo
    - 503: Servicio no listo
    """
    checks = {}
    overall_status = "ready"
    status_code = 200
    
    # ===== CHECK 1: CONFIGURACIÓN =====
    try:
        Config.validate()
        checks['config'] = 'ok'
    except Exception as e:
        checks['config'] = f'error: {str(e)}'
        overall_status = 'not_ready'
        status_code = 503
    
    # ===== CHECK 2: GEMINI API KEY =====
    try:
        if Config.GOOGLE_API_KEY and len(Config.GOOGLE_API_KEY) > 10:
            checks['gemini'] = 'ok'
        else:
            checks['gemini'] = 'not_configured'
            overall_status = 'not_ready'
            status_code = 503
    except Exception as e:
        checks['gemini'] = f'error: {str(e)}'
        overall_status = 'not_ready'
        status_code = 503
    
    # ===== CHECK 3: MCP CLIENT (OPCIONAL) =====
    try:
        # Intentar obtener cliente MCP (no inicializar aún)
        # Este check es opcional y no falla el readiness
        checks['mcp'] = 'not_checked'  # MCP se inicializa bajo demanda
    except Exception as e:
        checks['mcp'] = f'warning: {str(e)}'
    
    # ===== CHECK 4: DIRECTORIOS =====
    try:
        Config.ensure_directories()
        checks['directories'] = 'ok'
    except Exception as e:
        checks['directories'] = f'warning: {str(e)}'
    
    logger.info(f"Readiness check: {overall_status} - {checks}")
    
    return jsonify({
        'status': overall_status,
        'service': 'video-service',
        'checks': checks,
        'config': {
            'gemini_model': Config.GEMINI_MODEL,
            'max_frames': Config.MAX_FRAMES_PER_VIDEO,
            'rag_configured': bool(Config.RAG_API_URL)
        }
    }), status_code


@health_bp.route('/health/live', methods=['GET'])
def liveness_check():
    """
    Liveness check para Kubernetes.
    
    Indica si el proceso está vivo (sin verificar dependencias).
    
    Response:
    {
        "status": "alive"
    }
    
    Status: 200 OK
    """
    return jsonify({
        'status': 'alive',
        'service': 'video-service'
    }), 200
