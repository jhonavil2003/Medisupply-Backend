"""
Analyze Video Command
=====================

Command principal para orquestar el análisis completo de video.

Flujo:
1. Extraer frames del video (VideoProcessor)
2. Analizar con Gemini Vision (GeminiVisionService)
3. Construir query para RAG (QueryBuilder)
4. Consultar RAG vía MCP (MCPClientService)
5. Construir recomendación final (RecommendationBuilder)
6. Cleanup de recursos temporales
"""

import asyncio
import time
import logging
from typing import Dict, Any, Optional

from src.services.video_processor_service import VideoProcessorService
from src.services.gemini_vision_service import GeminiVisionService
from src.services.rag_http_client_service import get_rag_client
from src.errors.errors import ValidationError, ApiError, ExternalServiceError
from src.utils.config import Config

logger = logging.getLogger(__name__)


class AnalyzeVideoCommand:
    """
    Command para analizar video y recomendar productos.
    
    ORQUESTADOR PRINCIPAL del flujo de análisis.
    
    Responsabilidades:
    - Validar input del usuario
    - Coordinar todos los servicios
    - Gestionar errores y timeouts
    - Garantizar cleanup de recursos
    - Formatear respuesta final
    
    Patrón: Command Pattern (igual que microservicios Flask)
    """
    
    def __init__(self, video_url: str, analysis_type: str = "full"):
        """
        Inicializa el command.
        
        Args:
            video_url: URL del video a analizar
            analysis_type: Tipo de análisis ("full", "quick")
        
        Raises:
            ValidationError: Si los parámetros son inválidos
        """
        self.video_url = video_url
        self.analysis_type = analysis_type
        
        # Validar input
        self._validate_input()
        
        # Inicializar servicios
        self.video_processor = VideoProcessorService()
        self.gemini_service = GeminiVisionService()
        
        # RAG Client se inicializa bajo demanda (async)
        self.rag_client = None
        
        logger.info(
            f"AnalyzeVideoCommand initialized: "
            f"url={video_url[:50]}..., type={analysis_type}"
        )
    
    def _validate_input(self):
        """
        Valida los parámetros de entrada.
        
        Raises:
            ValidationError: Si hay errores de validación
        """
        if not self.video_url:
            raise ValidationError("video_url is required")
        
        if not isinstance(self.video_url, str):
            raise ValidationError("video_url must be a string")
        
        if not self.video_url.startswith(('http://', 'https://')):
            raise ValidationError(
                "video_url must be a valid URL (http:// or https://)"
            )
        
        valid_types = ["full", "quick"]
        if self.analysis_type not in valid_types:
            raise ValidationError(
                f"analysis_type must be one of: {', '.join(valid_types)}"
            )
    
    async def execute(self) -> Dict[str, Any]:
        """
        Ejecuta el análisis completo del video.
        
        FLUJO PRINCIPAL:
        1. Extraer frames del video
        2. Analizar frames con Gemini Vision
        3. Construir query optimizada para RAG
        4. Consultar RAG vía MCP
        5. Construir recomendaciones finales
        6. Cleanup (siempre, incluso con errores)
        
        Returns:
            Diccionario con análisis completo:
            {
                'status': 'success',
                'video_url': str,
                'video_analysis': {...},
                'rag_context': str,
                'recommendations': {...},
                'metadata': {...}
            }
        
        Raises:
            ValidationError: Si hay errores de validación
            ExternalServiceError: Si servicios externos fallan
            ApiError: Si hay errores generales
        """
        start_time = time.time()
        frame_paths = []
        
        try:
            logger.info("=" * 70)
            logger.info("🚀 STARTING VIDEO ANALYSIS PIPELINE")
            logger.info(f"   Video URL: {self.video_url}")
            logger.info(f"   Analysis Type: {self.analysis_type}")
            logger.info("=" * 70)
            
            # ===== PASO 1: EXTRAER FRAMES DEL VIDEO =====
            logger.info("\n🎬 STEP 1/5: Extracting video frames...")
            frame_paths = await self._extract_frames()
            logger.info(f"   ✅ Extracted {len(frame_paths)} frames")
            
            # ===== PASO 2: ANALIZAR CON GEMINI VISION =====
            logger.info("\n🤖 STEP 2/5: Analyzing frames with Gemini Vision...")
            video_analysis = await self._analyze_with_gemini(frame_paths)
            logger.info(
                f"   ✅ Analysis complete: "
                f"{len(video_analysis.get('detected_products', []))} products detected"
            )
            
            # ===== PASO 3: CONSTRUIR QUERY PARA RAG =====
            logger.info("\n📝 STEP 3/5: Building optimized RAG query...")
            rag_query = self._build_rag_query(video_analysis)
            logger.info(f"   ✅ Query built ({len(rag_query)} chars)")
            
            # ===== PASO 4: CONSULTAR RAG VÍA MCP =====
            logger.info("\n🔍 STEP 4/5: Querying RAG via MCP Client...")
            rag_context = await self._query_rag(rag_query)
            logger.info(f"   ✅ RAG context retrieved ({len(rag_context)} chars)")
            
            # ===== PASO 5: CONSTRUIR RECOMENDACIÓN FINAL =====
            logger.info("\n✨ STEP 5/5: Building final recommendations...")
            recommendations = self._build_recommendations(
                video_analysis,
                rag_context
            )
            logger.info("   ✅ Recommendations built")
            
            # ===== CALCULAR METADATA =====
            processing_time = time.time() - start_time
            
            logger.info("\n" + "=" * 70)
            logger.info(f"✅ VIDEO ANALYSIS COMPLETED SUCCESSFULLY")
            logger.info(f"   Processing time: {processing_time:.2f}s")
            logger.info(f"   Frames analyzed: {len(frame_paths)}")
            logger.info("=" * 70)
            
            # ===== CONSTRUIR RESPUESTA =====
            return {
                'status': 'success',
                'video_url': self.video_url,
                'video_analysis': video_analysis,
                'rag_context': rag_context,
                'recommendations': recommendations,
                'metadata': {
                    'frames_analyzed': len(frame_paths),
                    'processing_time_seconds': round(processing_time, 2),
                    'analysis_type': self.analysis_type,
                    'gemini_model': Config.GEMINI_MODEL,
                }
            }
            
        except ValidationError:
            # Re-lanzar errores de validación tal cual
            raise
            
        except ExternalServiceError as e:
            logger.error(f"❌ External service error: {str(e)}")
            raise
            
        except Exception as e:
            logger.error(
                f"❌ Unexpected error during video analysis: {str(e)}",
                exc_info=True
            )
            raise ApiError(
                f"Video analysis failed: {str(e)}",
                status_code=500
            )
            
        finally:
            # ===== CLEANUP: SIEMPRE SE EJECUTA =====
            if frame_paths:
                logger.info("\n🧹 CLEANUP: Removing temporary frames...")
                try:
                    self.video_processor.cleanup_frames(frame_paths)
                    logger.info("   ✅ Cleanup completed")
                except Exception as e:
                    logger.warning(f"   ⚠️ Cleanup warning: {str(e)}")
    
    async def _extract_frames(self) -> list:
        """
        Extrae frames del video.
        
        Returns:
            Lista de paths a frames extraídos
        
        Raises:
            ApiError: Si la extracción falla
        """
        try:
            # Ajustar max_frames según tipo de análisis
            max_frames = Config.MAX_FRAMES_PER_VIDEO
            if self.analysis_type == "quick":
                max_frames = max(3, max_frames // 2)
            
            frame_paths = await self.video_processor.extract_frames(
                self.video_url,
                max_frames=max_frames
            )
            
            if not frame_paths:
                raise ApiError(
                    "No frames could be extracted from video. "
                    "Video may be corrupted or in unsupported format."
                )
            
            return frame_paths
            
        except ValueError as e:
            # Errores de validación del video
            raise ValidationError(str(e))
        except Exception as e:
            raise ApiError(f"Frame extraction failed: {str(e)}")
    
    async def _analyze_with_gemini(self, frame_paths: list) -> Dict[str, Any]:
        """
        Analiza frames con Gemini Vision.
        
        Args:
            frame_paths: Paths a frames
        
        Returns:
            Análisis de Gemini
        
        Raises:
            ExternalServiceError: Si Gemini falla
        """
        try:
            analysis = await self.gemini_service.analyze_video_frames(frame_paths)
            
            # Validar análisis
            if not self.gemini_service.validate_analysis(analysis):
                logger.warning("Gemini analysis validation failed, using fallback")
                analysis = self._get_fallback_analysis()
            
            return analysis
            
        except ExternalServiceError:
            # Re-lanzar errores de servicio externo
            raise
        except Exception as e:
            raise ExternalServiceError(
                f"Gemini Vision analysis failed: {str(e)}",
                status_code=502
            )
    
    def _build_rag_query(self, video_analysis: Dict[str, Any]) -> str:
        """
        Construye query optimizada para el RAG.
        
        Combina:
        - Productos detectados
        - Categorías sugeridas
        - Contexto operativo
        - Oportunidades identificadas
        
        Args:
            video_analysis: Análisis de Gemini
        
        Returns:
            Query estructurada para RAG
        """
        detected = video_analysis.get('detected_products', [])
        categories = video_analysis.get('suggested_categories', [])
        context = video_analysis.get('context', '')
        opportunities = video_analysis.get('opportunities', [])
        
        # Construir query estructurada
        query_parts = []
        
        # Productos específicos
        if detected:
            products_str = ', '.join(detected[:5])  # Limitar a 5
            query_parts.append(f"Productos de interés: {products_str}")
        
        # Categorías
        if categories:
            categories_str = ', '.join(categories)
            query_parts.append(f"Categorías: {categories_str}")
        
        # Contexto
        if context:
            query_parts.append(f"Contexto: {context}")
        
        # Oportunidades
        if opportunities:
            opps_str = '. '.join(opportunities[:3])
            query_parts.append(f"Oportunidades identificadas: {opps_str}")
        
        # Unir todo
        query = "\n\n".join(query_parts)
        
        # Agregar instrucción final
        query += (
            "\n\nPor favor, proporciona información detallada sobre estos productos "
            "o alternativas similares disponibles en el catálogo de MediSupply, "
            "incluyendo especificaciones técnicas, precios y disponibilidad."
        )
        
        return query.strip()
    
    async def _query_rag(self, query: str) -> str:
        """
        Consulta el RAG vía MCP.
        
        Args:
            query: Query construida
        
        Returns:
            Contexto del RAG
        
        Raises:
            ExternalServiceError: Si MCP/RAG falla
        """
        try:
            # Obtener cliente RAG (singleton)
            if self.rag_client is None:
                self.rag_client = await get_rag_client()
            
            # Consultar RAG
            rag_context = await self.rag_client.query_rag(query)
            
            if not rag_context:
                logger.warning("RAG returned empty context")
                return "No se encontró información específica en el catálogo."
            
            return rag_context
            
        except Exception as e:
            logger.error(f"RAG query failed: {str(e)}")
            raise ExternalServiceError(
                f"Failed to query product catalog: {str(e)}",
                status_code=502
            )
    
    def _build_recommendations(
        self,
        video_analysis: Dict[str, Any],
        rag_context: str
    ) -> Dict[str, Any]:
        """
        Construye recomendaciones finales.
        
        Combina:
        - Análisis visual de Gemini
        - Información del catálogo (RAG)
        - Lógica de negocio de MediSupply
        
        Args:
            video_analysis: Análisis de Gemini
            rag_context: Contexto del RAG
        
        Returns:
            Diccionario con recomendaciones estructuradas
        """
        detected = video_analysis.get('detected_products', [])
        opportunities = video_analysis.get('opportunities', [])
        context = video_analysis.get('context', '')
        confidence = video_analysis.get('confidence', 0.0)
        
        # Construir reasoning
        reasoning_parts = []
        
        # Análisis visual
        if detected:
            reasoning_parts.append(
                f"**Productos detectados en video**: {', '.join(detected[:5])}"
            )
        
        # Contexto operativo
        if context:
            reasoning_parts.append(f"**Contexto operativo**: {context}")
        
        # Oportunidades
        if opportunities:
            opps_formatted = '\n'.join([f"- {opp}" for opp in opportunities[:5]])
            reasoning_parts.append(
                f"**Oportunidades identificadas**:\n{opps_formatted}"
            )
        
        # Información del catálogo
        rag_preview = rag_context[:800] if len(rag_context) > 800 else rag_context
        reasoning_parts.append(
            f"**Información del catálogo MediSupply**:\n{rag_preview}"
        )
        
        # Confidence
        confidence_pct = int(confidence * 100)
        reasoning_parts.append(
            f"\n**Confianza del análisis**: {confidence_pct}%"
        )
        
        reasoning = "\n\n".join(reasoning_parts)
        
        return {
            'products': detected,
            'opportunities': opportunities,
            'reasoning': reasoning,
            'rag_full_context': rag_context,
            'confidence_score': confidence,
            'actionable_insights': self._extract_insights(
                video_analysis,
                rag_context
            )
        }
    
    def _extract_insights(
        self,
        video_analysis: Dict[str, Any],
        rag_context: str
    ) -> list:
        """
        Extrae insights accionables para el equipo de ventas.
        
        Args:
            video_analysis: Análisis de Gemini
            rag_context: Contexto del RAG
        
        Returns:
            Lista de insights accionables
        """
        insights = []
        
        # Competencia detectada
        competitors = video_analysis.get('competitor_brands', [])
        if competitors:
            insights.append({
                'type': 'competition',
                'message': f"Competencia detectada: {', '.join(competitors)}",
                'action': 'Preparar propuesta comparativa de MediSupply'
            })
        
        # Productos faltantes
        opportunities = video_analysis.get('opportunities', [])
        for opp in opportunities:
            if 'faltante' in opp.lower() or 'agotado' in opp.lower():
                insights.append({
                    'type': 'stock_opportunity',
                    'message': opp,
                    'action': 'Contactar cliente para oferta inmediata'
                })
        
        # Confianza baja
        confidence = video_analysis.get('confidence', 1.0)
        if confidence < 0.5:
            insights.append({
                'type': 'low_confidence',
                'message': 'Análisis requiere validación manual',
                'action': 'Revisión por experto recomendada'
            })
        
        return insights
    
    def _get_fallback_analysis(self) -> Dict[str, Any]:
        """
        Análisis fallback cuando Gemini falla.
        
        Returns:
            Análisis básico por defecto
        """
        return {
            'detected_products': [],
            'competitor_brands': [],
            'context': 'Análisis automático no disponible',
            'user_needs': 'Requiere revisión manual',
            'suggested_categories': ['General'],
            'opportunities': ['Análisis manual recomendado'],
            'confidence': 0.0
        }
