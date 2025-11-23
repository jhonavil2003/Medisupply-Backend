"""Tests para AnalyzeVideoCommand"""

import pytest
from unittest.mock import Mock, patch

from src.commands.analyze_video_command import AnalyzeVideoCommand
from src.errors.errors import ValidationError


class TestAnalyzeVideoCommandInit:
    """Test suite para inicialización del command"""
    
    def test_initialization_with_valid_url(self):
        """Test inicialización con URL válida"""
        command = AnalyzeVideoCommand(
            video_url="https://example.com/video.mp4"
        )
        assert command.video_url == "https://example.com/video.mp4"
        assert command.analysis_type == "full"
    
    def test_initialization_with_custom_analysis_type(self):
        """Test inicialización con tipo de análisis personalizado"""
        command = AnalyzeVideoCommand(
            video_url="https://example.com/video.mp4",
            analysis_type="quick"
        )
        assert command.analysis_type == "quick"
    
    def test_initialization_creates_services(self):
        """Test que inicialización crea servicios"""
        command = AnalyzeVideoCommand(
            video_url="https://example.com/video.mp4"
        )
        assert command.video_processor is not None
        assert command.gemini_service is not None
    
    def test_initialization_fails_without_url(self):
        """Test que falla sin video_url"""
        with pytest.raises(ValidationError):
            AnalyzeVideoCommand(video_url="")
    
    def test_initialization_fails_with_invalid_url_type(self):
        """Test que falla con tipo inválido de URL"""
        with pytest.raises(ValidationError):
            AnalyzeVideoCommand(video_url=123)
    
    def test_initialization_fails_with_non_http_url(self):
        """Test que falla con URL no HTTP/HTTPS"""
        with pytest.raises(ValidationError):
            AnalyzeVideoCommand(video_url="ftp://example.com/video.mp4")
    
    def test_initialization_fails_with_invalid_analysis_type(self):
        """Test que falla con tipo de análisis inválido"""
        with pytest.raises(ValidationError):
            AnalyzeVideoCommand(
                video_url="https://example.com/video.mp4",
                analysis_type="invalid"
            )
    
    def test_rag_client_initialized_as_none(self):
        """Test que RAG client se inicializa como None"""
        command = AnalyzeVideoCommand(
            video_url="https://example.com/video.mp4"
        )
        assert command.rag_client is None
    
    def test_initialization_with_http_url(self):
        """Test inicialización con HTTP (sin S)"""
        command = AnalyzeVideoCommand(
            video_url="http://example.com/video.mp4"
        )
        assert command.video_url == "http://example.com/video.mp4"
    
    def test_analysis_type_defaults_to_full(self):
        """Test que analysis_type por defecto es 'full'"""
        command = AnalyzeVideoCommand(
            video_url="https://example.com/video.mp4"
        )
        assert command.analysis_type == "full"

