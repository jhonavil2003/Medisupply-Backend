"""

Endpoints para análisis de videos con IA.

Endpoints:
- POST /api/videos/analyze - Analizar video y recomendar productos
"""

from flask import Blueprint, request, jsonify
import asyncio
import logging

from src.commands.analyze_video_command import AnalyzeVideoCommand
from src.errors.errors import ValidationError, ApiError

logger = logging.getLogger(__name__)

# Crear Blueprint
video_analysis_bp = Blueprint('video_analysis', __name__)


@video_analysis_bp.route('/api/videos/analyze', methods=['POST'])
async def analyze_video():
    """
    Analizar video y generar recomendaciones de productos.
    
    ENDPOINT PRINCIPAL del Video Service.
    
    Request Body:
    {
        "video_url": "https://example.com/video.mp4",
        "analysis_type": "full"  // opcional: "full" | "quick"
    }
    
    Response:
    {
        "status": "success",
        "video_url": "...",
        "video_analysis": {
            "detected_products": [...],
            "context": "...",
            "opportunities": [...]
        },
        "rag_context": "...",
        "recommendations": {
            "products": [...],
            "reasoning": "...",
            "actionable_insights": [...]
        },
        "metadata": {
            "frames_analyzed": 10,
            "processing_time_seconds": 15.3,
            "gemini_model": "gemini-2.0-flash-exp"
        }
    }
    
    Status Codes:
    - 200: Análisis completado exitosamente
    - 400: Error de validación (video_url inválido)
    - 502: Error de servicio externo (Gemini, RAG)
    - 500: Error interno del servidor
    
    Example:
        curl -X POST http://localhost:3004/api/videos/analyze \\
             -H "Content-Type: application/json" \\
             -d '{"video_url": "https://example.com/factory.mp4"}'
    """
    try:
        # ===== VALIDAR REQUEST =====
        if not request.is_json:
            raise ValidationError("Content-Type must be application/json")
        
        data = request.get_json()
        
        if not data:
            raise ValidationError("Request body is required")
        
        video_url = data.get('video_url')
        if not video_url:
            raise ValidationError("video_url is required")
        
        analysis_type = data.get('analysis_type', 'full')
        
        logger.info(
            f"📥 Received video analysis request: "
            f"url={video_url[:50]}..., type={analysis_type}"
        )
        
        # ===== EJECUTAR COMMAND =====
        command = AnalyzeVideoCommand(
            video_url=video_url,
            analysis_type=analysis_type
        )
        
        # Ejecutar análisis (asíncrono)
        result = await command.execute()
        
        logger.info(f"📤 Video analysis completed successfully")
        
        # ===== RESPUESTA =====
        return jsonify(result), 200
        
    except ValidationError as e:
        logger.warning(f"Validation error: {e.message}")
        raise
        
    except ApiError as e:
        logger.error(f"API error: {e.message}")
        raise
        
    except Exception as e:
        logger.error(f"Unexpected error in analyze_video endpoint: {str(e)}", exc_info=True)
        raise ApiError(
            f"Failed to analyze video: {str(e)}",
            status_code=500
        )


@video_analysis_bp.route('/api/videos/status/<analysis_id>', methods=['GET'])
async def get_analysis_status(analysis_id: str):
    """
    Obtener estado de análisis (para futuras implementaciones).
    
    Endpoint placeholder para análisis asíncrono con IDs.
    Actualmente no implementado (análisis son síncronos).
    
    Args:
        analysis_id: ID del análisis
    
    Response:
    {
        "status": "not_implemented",
        "message": "Analysis tracking not yet implemented"
    }
    """
    logger.info(f"Status check requested for analysis: {analysis_id}")
    
    return jsonify({
        'status': 'not_implemented',
        'message': 'Analysis tracking not yet implemented. All analyses are currently synchronous.',
        'analysis_id': analysis_id
    }), 501


@video_analysis_bp.route('/api/videos/supported-formats', methods=['GET'])
def get_supported_formats():
    """
    Listar formatos de video soportados.
    
    Response:
    {
        "supported_formats": [
            "mp4", "avi", "mov", "mkv", "webm"
        ],
        "max_file_size_mb": 100,
        "recommended_duration_seconds": 30
    }
    """
    return jsonify({
        'supported_formats': [
            'mp4',
            'avi',
            'mov',
            'mkv',
            'webm',
            'flv'
        ],
        'max_file_size_mb': 100,
        'recommended_duration_seconds': 30,
        'max_frames_extracted': 10,
        'notes': [
            'Videos must be accessible via HTTP/HTTPS URL',
            'Large videos may take longer to process',
            'Optimal duration: 10-60 seconds'
        ]
    }), 200
