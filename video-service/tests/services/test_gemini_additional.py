"""Tests adicionales para gemini_vision_service"""

import pytest
from unittest.mock import Mock, patch
import json

from src.services.gemini_vision_service import GeminiVisionService


class TestGeminiVisionAdditional:
    """Tests adicionales para cobertura"""
    
    def test_parse_json_response_with_markdown(self):
        """Test parsing de respuesta con markdown"""
        service = GeminiVisionService()
        
        response_with_markdown = """```json
{
    "detected_products": ["Product A"],
    "context": "Test",
    "user_needs": "Needs",
    "suggested_categories": ["Cat1"],
    "opportunities": ["Opp1"],
    "competitor_brands": [],
    "confidence": 0.8
}
```"""
        
        result = service._parse_gemini_response(response_with_markdown)
        assert 'detected_products' in result
        assert result['detected_products'] == ["Product A"]
    
    def test_parse_json_response_plain(self):
        """Test parsing de respuesta JSON plano"""
        service = GeminiVisionService()
        
        plain_json = '''{
            "detected_products": ["Product B"],
            "context": "Test",
            "user_needs": "Needs",
            "suggested_categories": ["Cat1"],
            "opportunities": ["Opp1"],
            "competitor_brands": [],
            "confidence": 0.9
        }'''
        
        result = service._parse_gemini_response(plain_json)
        assert result['detected_products'] == ["Product B"]
    
    def test_fallback_text_analysis(self):
        """Test análisis de fallback con texto plano"""
        service = GeminiVisionService()
        
        text = "Product A, Product B mentioned. Factory setting with medical equipment."
        
        result = service._fallback_text_analysis(text)
        
        assert 'detected_products' in result
        assert 'context' in result
        assert 'confidence' in result
        assert result['confidence'] < 0.7  # Baja confianza en fallback
    
    def test_fallback_empty_text(self):
        """Test fallback con texto vacío"""
        service = GeminiVisionService()
        
        result = service._fallback_text_analysis("")
        
        assert result['detected_products'] == []
        assert result['confidence'] == 0.3
    
    @pytest.mark.asyncio
    @patch('os.path.exists', return_value=True)
    @patch('builtins.open', create=True)
    async def test_prepare_multimodal_limits_frames(self, mock_open_fn, mock_exists):
        """Test que _prepare_multimodal_content limita frames"""
        service = GeminiVisionService()
        
        # Crear 25 frames (más del límite de 20)
        frame_paths = [f"/tmp/frame{i}.jpg" for i in range(25)]
        
        mock_file = Mock()
        mock_file.__enter__ = Mock(return_value=mock_file)
        mock_file.__exit__ = Mock(return_value=False)
        mock_file.read = Mock(return_value=b'fake_image_data')
        mock_open_fn.return_value = mock_file
        
        content = await service._prepare_multimodal_content("Test prompt", frame_paths)
        
        # Contar cuántos elementos de imagen hay (no más de 20)
        image_count = sum(1 for item in content if isinstance(item, dict) and item.get('type') == 'image_url')
        assert image_count <= 20
    
    def test_build_analysis_prompt_contains_keywords(self):
        """Test que prompt contiene palabras clave"""
        service = GeminiVisionService()
        
        prompt = service._build_analysis_prompt()
        
        assert "JSON" in prompt
        assert "detected_products" in prompt
        assert "context" in prompt
        assert "MediSupply" in prompt
        assert "opportunities" in prompt
    
    def test_initialization_uses_config(self):
        """Test que inicialización usa Config"""
        with patch('src.services.gemini_vision_service.Config') as mock_config:
            mock_config.GEMINI_MODEL = "test-model"
            mock_config.GEMINI_TEMPERATURE = 0.5
            mock_config.GEMINI_MAX_OUTPUT_TOKENS = 2000
            mock_config.GOOGLE_API_KEY = "test-key"
            
            service = GeminiVisionService()
            
            assert service.model is not None
    
    @pytest.mark.asyncio
    async def test_analyze_validates_empty_frame_list(self):
        """Test que valida lista vacía de frames"""
        service = GeminiVisionService()
        
        with pytest.raises(ValueError, match="No frames provided"):
            await service.analyze_video_frames([])
    
    def test_parse_response_handles_extra_fields(self):
        """Test que parsing maneja campos extra"""
        service = GeminiVisionService()
        
        response = '''{
            "detected_products": ["A"],
            "context": "Test",
            "user_needs": "Needs",
            "suggested_categories": ["C1"],
            "opportunities": ["O1"],
            "competitor_brands": ["B1"],
            "confidence": 0.8,
            "extra_field": "ignored"
        }'''
        
        result = service._parse_gemini_response(response)
        assert 'detected_products' in result
        assert result['detected_products'] == ["A"]
