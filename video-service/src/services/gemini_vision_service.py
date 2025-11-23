"""Servicio para análisis de imágenes con Gemini Vision."""

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
import base64
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from src.utils.config import Config
from src.errors.errors import ExternalServiceError

logger = logging.getLogger(__name__)


class GeminiVisionService:
    """Servicio para análisis de contenido visual con Gemini Vision."""
    
    def __init__(
        self,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ):
        """
        Inicializa el servicio de Gemini Vision.
        
        Args:
            model: Nombre del modelo (default: Config.GEMINI_MODEL)
            temperature: Temperatura para generación (default: Config.GEMINI_TEMPERATURE)
            max_tokens: Máximo de tokens (default: Config.GEMINI_MAX_TOKENS)
        """
        self.model_name = model or Config.GEMINI_MODEL
        self.temperature = temperature or Config.GEMINI_TEMPERATURE
        self.max_tokens = max_tokens or Config.GEMINI_MAX_TOKENS
        
        try:
            self.model = ChatGoogleGenerativeAI(
                model=self.model_name,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            logger.info(
                f"GeminiVisionService initialized: "
                f"model={self.model_name}, temp={self.temperature}"
            )
        except Exception as e:
            logger.error(f"Failed to initialize Gemini model: {str(e)}")
            raise ExternalServiceError(
                f"Cannot initialize Gemini Vision model: {str(e)}",
                status_code=500
            )
    
    async def analyze_video_frames(self, frame_paths: List[str]) -> Dict[str, Any]:
        """
        Analiza frames del video con Gemini Vision.
        
        El análisis se enfoca en identificar:
        - Productos visibles (marcas, categorías)
        - Equipos y maquinaria (estado, necesidades)
        - Contexto operativo (tipo de industria, proceso)
        - Oportunidades de venta (faltantes, competencia)
        
        Args:
            frame_paths: Lista de rutas a imágenes de frames
        
        Returns:
            Diccionario con análisis estructurado:
            {
                'detected_products': ['producto1', 'producto2'],
                'context': 'descripción del contexto industrial',
                'user_needs': 'necesidades inferidas del cliente',
                'suggested_categories': ['categoría1', 'categoría2'],
                'opportunities': ['oportunidad1', 'oportunidad2'],
                'confidence': 0.0-1.0
            }
        
        Raises:
            ExternalServiceError: Si Gemini API falla
            ValueError: Si no hay frames para analizar
        
        Example:
            >>> service = GeminiVisionService()
            >>> frames = ['frame1.jpg', 'frame2.jpg']
            >>> analysis = await service.analyze_video_frames(frames)
            >>> print(analysis['detected_products'])
            ['Jarabe de Glucosa', 'Harina de Trigo']
        """
        if not frame_paths:
            raise ValueError("No frames provided for analysis")
        
        logger.info(f"🤖 Starting Gemini Vision analysis of {len(frame_paths)} frames...")
        
        try:
            # ===== PASO 1: Construir prompt especializado =====
            prompt = self._build_analysis_prompt()
            
            # ===== PASO 2: Preparar contenido multimodal =====
            content = await self._prepare_multimodal_content(prompt, frame_paths)
            
            # ===== PASO 3: Invocar Gemini =====
            logger.info("   Sending request to Gemini API...")
            message = HumanMessage(content=content)
            response = self.model.invoke([message])
            
            logger.info(f"   ✓ Received response from Gemini ({len(response.content)} chars)")
            
            # ===== PASO 4: Parsear respuesta JSON =====
            analysis = self._parse_gemini_response(response.content)
            
            logger.info(
                f"✅ Gemini analysis completed: "
                f"{len(analysis.get('detected_products', []))} products detected"
            )
            
            return analysis
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response as JSON: {str(e)}")
            # Fallback: intentar extraer información del texto plano
            return self._fallback_text_analysis(response.content if 'response' in locals() else "")
        
        except Exception as e:
            logger.error(f"❌ Gemini Vision analysis failed: {str(e)}")
            raise ExternalServiceError(
                f"Gemini Vision analysis failed: {str(e)}",
                status_code=502
            )
    
    def _build_analysis_prompt(self) -> str:
        """
        Construye el prompt especializado para análisis de suministros médicos.
        
        OPTIMIZADO para MediSupply:
        - Enfoque en productos químicos y materias primas
        - Detección de competencia y oportunidades
        - Contexto de logística y distribución médica
        
        Returns:
            Prompt completo para Gemini
        """
        return """
# ROL: Experto en Logística de Suministros Médicos e Industriales

Eres un analista especializado en identificar oportunidades de venta para **MediSupply**, 
una empresa distribuidora de materias primas químicas, productos farmacéuticos y suministros 
para la industria alimentaria, cosmética y médica.

## OBJETIVO DE ANÁLISIS

Analiza estas imágenes de un video tomado en una instalación industrial/médica y detecta:

### 1. PRODUCTOS VISIBLES
- Materias primas químicas (edulcorantes, conservantes, etc.)
- Productos farmacéuticos o de laboratorio
- Equipos y maquinaria industrial
- Marcas de competencia (IMPORTANTE: identifica proveedores actuales)
- Empaques, etiquetas, contenedores visibles

### 2. CONTEXTO OPERATIVO
- Tipo de industria: ¿Panadería? ¿Farmacia? ¿Laboratorio? ¿Hospital?
- Proceso productivo visible: ¿Qué están fabricando/preparando?
- Escala de operación: ¿Artesanal? ¿Industrial?
- Condiciones de almacenamiento: ¿Refrigerado? ¿Temperatura ambiente?

### 3. OPORTUNIDADES DE VENTA (CRÍTICO)
- **Productos faltantes o agotados** en estanterías
- **Equipos desgastados** que requieren mantenimiento
- **Marcas de competencia** que podemos reemplazar
- **Necesidades no cubiertas** basadas en el proceso visible
- **Cross-selling**: Si usan producto A, podrían necesitar producto B

### 4. CATEGORÍAS PRIORITARIAS DE MEDISUPPLY
- Edulcorantes (jarabe de glucosa, fructosa, maltodextrina)
- Harinas y almidones (trigo, maíz, modificados)
- Conservantes y antimicrobianos
- Colorantes alimentarios
- Aromas y saborizantes
- Productos de limpieza industrial
- Material de laboratorio

## FORMATO DE RESPUESTA

**IMPORTANTE**: Responde ÚNICAMENTE con un objeto JSON válido (sin markdown, sin explicaciones adicionales):

```json
{
  "detected_products": [
    "Nombre exacto del producto 1",
    "Nombre exacto del producto 2"
  ],
  "competitor_brands": [
    "Marca competidora visible 1",
    "Marca competidora visible 2"
  ],
  "context": "Descripción concisa del contexto industrial (máximo 100 palabras)",
  "user_needs": "Necesidades inferidas del cliente basadas en lo visible (máximo 80 palabras)",
  "suggested_categories": [
    "Categoría 1 de MediSupply",
    "Categoría 2 de MediSupply"
  ],
  "opportunities": [
    "Oportunidad de venta específica 1",
    "Oportunidad de venta específica 2",
    "Oportunidad de venta específica 3"
  ],
  "confidence": 0.85
}
```

## INSTRUCCIONES ADICIONALES

- **Sé específico con nombres técnicos** de productos químicos
- **Identifica marcas visibles** aunque sean de la competencia
- **Prioriza oportunidades de alto valor** (productos faltantes, necesidades urgentes)
- **El score de confidence** (0-1) debe reflejar qué tan clara es la información visual
- Si no detectas productos específicos, enfócate en el **contexto y necesidades**

Analiza ahora las imágenes proporcionadas y responde con el JSON.
""".strip()
    
    async def _prepare_multimodal_content(
        self,
        prompt: str,
        frame_paths: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Prepara contenido multimodal para Gemini.
        
        Combina prompt de texto con imágenes codificadas en base64.
        
        Args:
            prompt: Prompt de texto
            frame_paths: Paths a frames
        
        Returns:
            Lista de contenido para HumanMessage
        """
        content = [{"type": "text", "text": prompt}]
        
        # Limitar frames para no exceder límites de API
        max_frames_to_send = min(len(frame_paths), 10)
        selected_frames = frame_paths[:max_frames_to_send]
        
        logger.info(f"   Encoding {len(selected_frames)} frames to base64...")
        
        for i, frame_path in enumerate(selected_frames):
            try:
                # Validar que el archivo existe
                if not Path(frame_path).exists():
                    logger.warning(f"   ⚠️ Frame not found: {frame_path}")
                    continue
                
                # Leer y codificar imagen
                with open(frame_path, "rb") as img_file:
                    image_data = base64.b64encode(img_file.read()).decode('utf-8')
                
                # Agregar imagen al contenido
                content.append({
                    "type": "image_url",
                    "image_url": f"data:image/jpeg;base64,{image_data}"
                })
                
                logger.debug(f"   ✓ Frame {i+1} encoded successfully")
                
            except Exception as e:
                logger.warning(f"   ⚠️ Could not encode frame {frame_path}: {e}")
                continue
        
        logger.info(f"   ✓ Prepared {len(content)-1} images for analysis")
        return content
    
    def _parse_gemini_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parsea la respuesta de Gemini como JSON.
        
        Maneja diferentes formatos:
        - JSON puro
        - JSON dentro de markdown code blocks
        - JSON con texto adicional
        
        Args:
            response_text: Respuesta de Gemini
        
        Returns:
            Diccionario con análisis estructurado
        
        Raises:
            json.JSONDecodeError: Si no se puede parsear JSON
        """
        # Intentar parsear directamente
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            pass
        
        # Buscar JSON dentro de markdown code blocks
        if "```json" in response_text:
            start = response_text.find("```json") + 7
            end = response_text.find("```", start)
            json_str = response_text[start:end].strip()
            return json.loads(json_str)
        
        # Buscar JSON sin markdown
        if "```" in response_text:
            start = response_text.find("```") + 3
            end = response_text.find("```", start)
            json_str = response_text[start:end].strip()
            return json.loads(json_str)
        
        # Intentar encontrar objeto JSON en el texto
        start = response_text.find("{")
        end = response_text.rfind("}") + 1
        if start >= 0 and end > start:
            json_str = response_text[start:end]
            return json.loads(json_str)
        
        # Si todo falla, lanzar error
        raise json.JSONDecodeError("No valid JSON found in response", response_text, 0)
    
    def _fallback_text_analysis(self, text: str) -> Dict[str, Any]:
        """
        Análisis fallback cuando JSON parsing falla.
        
        Extrae información básica del texto plano.
        
        Args:
            text: Respuesta de texto de Gemini
        
        Returns:
            Diccionario con análisis básico
        """
        logger.warning("Using fallback text analysis (JSON parsing failed)")
        
        return {
            'detected_products': [],
            'competitor_brands': [],
            'context': text[:200] if text else "No context available",
            'user_needs': "Unable to determine specific needs from video",
            'suggested_categories': ["General"],
            'opportunities': ["Manual review recommended"],
            'confidence': 0.3,
            'raw_response': text[:500]
        }
    
    def validate_analysis(self, analysis: Dict[str, Any]) -> bool:
        """
        Valida que el análisis tenga la estructura esperada.
        
        Args:
            analysis: Análisis de Gemini
        
        Returns:
            True si es válido, False si no
        """
        required_fields = [
            'detected_products',
            'context',
            'user_needs',
            'suggested_categories',
            'confidence'
        ]
        
        for field in required_fields:
            if field not in analysis:
                logger.warning(f"Analysis missing required field: {field}")
                return False
        
        # Validar tipos
        if not isinstance(analysis['detected_products'], list):
            return False
        if not isinstance(analysis['suggested_categories'], list):
            return False
        if not isinstance(analysis['confidence'], (int, float)):
            return False
        
        return True
