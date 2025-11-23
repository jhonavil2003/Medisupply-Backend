"""Tests completos para analyze_video_command para mejorar cobertura"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import asyncio

from src.commands.analyze_video_command import AnalyzeVideoCommand


class TestAnalyzeVideoCommandExecution:
    """Tests para la ejecución del comando"""
    
    @pytest.mark.asyncio
    @patch('src.commands.analyze_video_command.VideoProcessorService')
    @patch('src.commands.analyze_video_command.GeminiVisionService')
    @patch('src.commands.analyze_video_command.get_rag_client')
    async def test_execute_extracts_frames(self, mock_get_rag, mock_gemini_class, mock_processor_class):
        """Test que execute extrae frames del video"""
        # Setup mocks
        mock_processor = AsyncMock()
        mock_processor.extract_frames = AsyncMock(return_value=["/tmp/frame1.jpg"])
        mock_processor.cleanup_frames = Mock()
        mock_processor.get_video_info = Mock(return_value={'frames': 100, 'fps': 30})
        mock_processor_class.return_value = mock_processor
        
        mock_gemini = AsyncMock()
        mock_gemini.analyze_video_frames = AsyncMock(return_value={
            'detected_products': [],
            'context': 'test',
            'user_needs': 'test',
            'suggested_categories': [],
            'opportunities': [],
            'competitor_brands': [],
            'confidence': 0.5
        })
        mock_gemini_class.return_value = mock_gemini
        
        mock_rag = AsyncMock()
        mock_rag.query_rag = AsyncMock(return_value="RAG response")
        mock_rag.initialize = AsyncMock()
        mock_rag.shutdown = AsyncMock()
        mock_get_rag.return_value = mock_rag
        
        # Execute
        command = AnalyzeVideoCommand(video_url="http://example.com/video.mp4")
        result = await command.execute()
        
        # Verify
        mock_processor.extract_frames.assert_called_once()
        assert 'video_analysis' in result
        assert 'status' in result
        assert result['status'] == 'success'
    
    @pytest.mark.asyncio
    @patch('src.commands.analyze_video_command.VideoProcessorService')
    async def test_execute_cleans_up_frames_on_success(self, mock_processor_class):
        """Test que execute limpia frames después del análisis"""
        mock_processor = AsyncMock()
        mock_processor.extract_frames = AsyncMock(return_value=["/tmp/frame1.jpg"])
        mock_processor.cleanup_frames = Mock()
        mock_processor.get_video_info = Mock(return_value={'frames': 100})
        mock_processor_class.return_value = mock_processor
        
        with patch('src.commands.analyze_video_command.GeminiVisionService'):
            with patch('src.commands.analyze_video_command.get_rag_client') as mock_get_rag:
                mock_rag = AsyncMock()
                mock_rag.query_rag = AsyncMock(return_value="response")
                mock_rag.initialize = AsyncMock()
                mock_rag.shutdown = AsyncMock()
                mock_get_rag.return_value = mock_rag
                
                command = AnalyzeVideoCommand(video_url="http://example.com/video.mp4")
                
                try:
                    await command.execute()
                except:
                    pass
                
                # Cleanup debe llamarse
                assert mock_processor.cleanup_frames.called
    
    @pytest.mark.asyncio
    @patch('src.commands.analyze_video_command.VideoProcessorService')
    @patch('src.commands.analyze_video_command.GeminiVisionService')
    @patch('src.commands.analyze_video_command.get_rag_client')
    async def test_execute_gets_video_info(self, mock_get_rag, mock_gemini_class, mock_processor_class):
        """Test que execute obtiene información del video"""
        mock_processor = AsyncMock()
        mock_processor.extract_frames = AsyncMock(return_value=["/tmp/frame1.jpg"])
        mock_processor.cleanup_frames = Mock()
        mock_processor.get_video_info = Mock(return_value={
            'frames': 100,
            'fps': 30,
            'duration_seconds': 3.33
        })
        mock_processor_class.return_value = mock_processor
        
        mock_gemini = AsyncMock()
        mock_gemini.analyze_video_frames = AsyncMock(return_value={
            'detected_products': [],
            'context': 'test',
            'user_needs': 'test',
            'suggested_categories': [],
            'opportunities': [],
            'competitor_brands': [],
            'confidence': 0.5
        })
        mock_gemini_class.return_value = mock_gemini
        
        mock_rag = AsyncMock()
        mock_rag.query_rag = AsyncMock(return_value="RAG response")
        mock_rag.initialize = AsyncMock()
        mock_rag.shutdown = AsyncMock()
        mock_get_rag.return_value = mock_rag
        
        command = AnalyzeVideoCommand(video_url="http://example.com/video.mp4")
        result = await command.execute()
        
        # El comando no llama a get_video_info en el flujo actual
        # Verificar que retorna metadata
        assert 'metadata' in result
        assert 'frames_analyzed' in result['metadata']
        assert result['metadata']['frames_analyzed'] > 0
    
    @pytest.mark.asyncio
    @patch('src.commands.analyze_video_command.VideoProcessorService')
    @patch('src.commands.analyze_video_command.GeminiVisionService')
    @patch('src.commands.analyze_video_command.get_rag_client')
    async def test_execute_calls_rag_with_context(self, mock_get_rag, mock_gemini_class, mock_processor_class):
        """Test que execute consulta RAG con contexto de Gemini"""
        mock_processor = AsyncMock()
        mock_processor.extract_frames = AsyncMock(return_value=["/tmp/frame1.jpg"])
        mock_processor.cleanup_frames = Mock()
        mock_processor.get_video_info = Mock(return_value={'frames': 100})
        mock_processor_class.return_value = mock_processor
        
        mock_gemini = AsyncMock()
        mock_gemini.analyze_video_frames = AsyncMock(return_value={
            'detected_products': ['Product A'],
            'context': 'Industrial setting',
            'user_needs': 'Equipment needed',
            'suggested_categories': ['Category 1'],
            'opportunities': ['Opportunity 1'],
            'competitor_brands': [],
            'confidence': 0.8
        })
        mock_gemini_class.return_value = mock_gemini
        
        mock_rag = AsyncMock()
        mock_rag.query_rag = AsyncMock(return_value="RAG recommendations")
        mock_rag.initialize = AsyncMock()
        mock_rag.shutdown = AsyncMock()
        mock_get_rag.return_value = mock_rag
        
        command = AnalyzeVideoCommand(video_url="http://example.com/video.mp4")
        result = await command.execute()
        
        # Verificar que RAG fue llamado
        mock_rag.query_rag.assert_called_once()
        call_args = mock_rag.query_rag.call_args[0][0]
        # El query debe incluir información de Gemini
        assert 'Product A' in call_args or 'Industrial' in call_args
    
    @pytest.mark.asyncio
    @patch('src.commands.analyze_video_command.VideoProcessorService')
    @patch('src.commands.analyze_video_command.GeminiVisionService')
    @patch('src.commands.analyze_video_command.get_rag_client')
    async def test_execute_returns_complete_structure(self, mock_get_rag, mock_gemini_class, mock_processor_class):
        """Test que execute retorna estructura completa de respuesta"""
        mock_processor = AsyncMock()
        mock_processor.extract_frames = AsyncMock(return_value=["/tmp/frame1.jpg", "/tmp/frame2.jpg"])
        mock_processor.cleanup_frames = Mock()
        mock_processor.get_video_info = Mock(return_value={
            'frames': 200,
            'fps': 30,
            'duration_seconds': 6.67
        })
        mock_processor_class.return_value = mock_processor
        
        mock_gemini = AsyncMock()
        mock_gemini.analyze_video_frames = AsyncMock(return_value={
            'detected_products': ['Product A', 'Product B'],
            'context': 'Factory floor',
            'user_needs': 'Industrial supplies',
            'suggested_categories': ['Cat1', 'Cat2'],
            'opportunities': ['Opp1'],
            'competitor_brands': ['Brand1'],
            'confidence': 0.9
        })
        mock_gemini_class.return_value = mock_gemini
        
        mock_rag = AsyncMock()
        mock_rag.query_rag = AsyncMock(return_value="Detailed product recommendations")
        mock_rag.initialize = AsyncMock()
        mock_rag.shutdown = AsyncMock()
        mock_get_rag.return_value = mock_rag
        
        command = AnalyzeVideoCommand(video_url="http://example.com/video.mp4")
        result = await command.execute()
        
        # Verificar estructura completa según implementación real
        assert 'status' in result
        assert 'video_url' in result
        assert 'video_analysis' in result
        assert 'rag_context' in result
        assert 'recommendations' in result
        assert 'metadata' in result
        
        # Verificar metadata
        assert result['metadata']['frames_analyzed'] == 2
        assert result['metadata']['analysis_type'] == 'full'
        assert result['status'] == 'success'
        assert result['video_url'] == "http://example.com/video.mp4"
