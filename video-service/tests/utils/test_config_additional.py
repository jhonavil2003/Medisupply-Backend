"""Tests adicionales para Config"""

import pytest
from unittest.mock import patch
import os

from src.utils.config import Config


class TestConfigAdditional:
    """Tests adicionales para cobertura"""
    
    def test_config_flask_env(self):
        """Test que FLASK_ENV está configurado"""
        assert hasattr(Config, 'FLASK_ENV')
        assert Config.FLASK_ENV in ['development', 'production', 'testing']
    
    def test_config_service_port(self):
        """Test que SERVICE_PORT es un entero"""
        assert hasattr(Config, 'SERVICE_PORT')
        assert isinstance(Config.SERVICE_PORT, int)
        assert Config.SERVICE_PORT > 0
    
    def test_config_host(self):
        """Test que HOST está configurado"""
        assert hasattr(Config, 'HOST')
        assert isinstance(Config.HOST, str)
    
    def test_config_debug_flag(self):
        """Test que DEBUG es booleano"""
        assert hasattr(Config, 'DEBUG')
        assert isinstance(Config.DEBUG, bool)
    
    def test_config_rag_mcp_server_path(self):
        """Test que RAG_MCP_SERVER_PATH existe"""
        assert hasattr(Config, 'RAG_MCP_SERVER_PATH')
        assert isinstance(Config.RAG_MCP_SERVER_PATH, str)
    
    def test_config_max_frames_per_video(self):
        """Test que MAX_FRAMES_PER_VIDEO es positivo"""
        assert hasattr(Config, 'MAX_FRAMES_PER_VIDEO')
        assert Config.MAX_FRAMES_PER_VIDEO > 0
    
    def test_config_frame_extraction_interval(self):
        """Test que FRAME_EXTRACTION_INTERVAL existe"""
        assert hasattr(Config, 'FRAME_EXTRACTION_INTERVAL')
        assert Config.FRAME_EXTRACTION_INTERVAL > 0
    
    def test_config_upload_folder(self):
        """Test que UPLOAD_FOLDER está configurado"""
        assert hasattr(Config, 'UPLOAD_FOLDER')
        assert isinstance(Config.UPLOAD_FOLDER, str)
        assert len(Config.UPLOAD_FOLDER) > 0
    
    def test_config_max_video_size_mb(self):
        """Test que MAX_VIDEO_SIZE_MB es positivo"""
        assert hasattr(Config, 'MAX_VIDEO_SIZE_MB')
        assert Config.MAX_VIDEO_SIZE_MB > 0
    
    def test_config_gemini_model(self):
        """Test que GEMINI_MODEL está configurado"""
        assert hasattr(Config, 'GEMINI_MODEL')
        assert 'gemini' in Config.GEMINI_MODEL.lower()
    
    def test_config_gemini_temperature(self):
        """Test que GEMINI_TEMPERATURE está en rango válido"""
        assert hasattr(Config, 'GEMINI_TEMPERATURE')
        assert 0 <= Config.GEMINI_TEMPERATURE <= 2.0
    
    def test_config_gemini_max_tokens(self):
        """Test que GEMINI_MAX_TOKENS es positivo"""
        assert hasattr(Config, 'GEMINI_MAX_TOKENS')
        assert Config.GEMINI_MAX_TOKENS > 0
