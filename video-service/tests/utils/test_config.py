"""Tests para Config Utils"""

import pytest
import os
from pathlib import Path
from src.utils.config import Config


class TestConfig:
    """Test suite para Config"""
    
    def test_config_has_required_attributes(self):
        """Test que Config tiene los atributos requeridos"""
        assert hasattr(Config, 'GOOGLE_API_KEY')
        assert hasattr(Config, 'GEMINI_MODEL')
        assert hasattr(Config, 'MAX_FRAMES_PER_VIDEO')
        assert hasattr(Config, 'UPLOAD_DIR')
        assert hasattr(Config, 'RAG_API_URL')
    
    def test_max_frames_is_integer(self):
        """Test que MAX_FRAMES es un entero"""
        assert isinstance(Config.MAX_FRAMES_PER_VIDEO, int)
        assert Config.MAX_FRAMES_PER_VIDEO > 0
    
    def test_upload_dir_is_path(self):
        """Test que UPLOAD_DIR es un Path"""
        assert isinstance(Config.UPLOAD_DIR, Path)
    
    def test_gemini_temperature_in_range(self):
        """Test que temperatura está en rango válido"""
        assert 0.0 <= Config.GEMINI_TEMPERATURE <= 1.0
    
    def test_gemini_max_tokens_positive(self):
        """Test que max tokens es positivo"""
        assert Config.GEMINI_MAX_TOKENS > 0
    
    def test_validate_with_valid_config(self, monkeypatch):
        """Test validación con configuración válida"""
        monkeypatch.setenv('GOOGLE_API_KEY', 'test_key_123')
        # No debe lanzar excepción
        Config.validate()
    
    def test_google_api_key_is_set(self):
        """Test que GOOGLE_API_KEY está configurado"""
        assert hasattr(Config, 'GOOGLE_API_KEY')
        assert Config.GOOGLE_API_KEY is not None
        assert len(Config.GOOGLE_API_KEY) > 0
    
    def test_ensure_directories_creates_upload_dir(self, tmp_path, monkeypatch):
        """Test que ensure_directories crea directorios"""
        test_dir = tmp_path / "test_uploads"
        monkeypatch.setattr(Config, 'UPLOAD_DIR', test_dir)
        
        Config.ensure_directories()
        
        assert test_dir.exists()
        assert test_dir.is_dir()
    
    def test_config_has_rag_api_url(self):
        """Test que Config tiene RAG_API_URL configurado"""
        assert hasattr(Config, 'RAG_API_URL')
        assert isinstance(Config.RAG_API_URL, str)
        assert len(Config.RAG_API_URL) > 0
    
    def test_rag_api_url_format(self):
        """Test formato de RAG API URL"""
        if Config.RAG_API_URL:
            assert Config.RAG_API_URL.startswith('http')
