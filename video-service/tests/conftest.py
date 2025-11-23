import pytest
import os
import sys
from pathlib import Path

# Agregar src al path para imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

# Mock environment variables para tests
os.environ.setdefault('GOOGLE_API_KEY', 'test_api_key_mock')
os.environ.setdefault('RAG_MCP_SERVER_PATH', '/tmp/mock_server.py')
os.environ.setdefault('FLASK_ENV', 'testing')
os.environ.setdefault('UPLOAD_FOLDER', '/tmp/test_uploads')


@pytest.fixture(scope='session')
def test_config():
    """Configuración para tests"""
    return {
        'TESTING': True,
        'GOOGLE_API_KEY': 'test_key',
        'MAX_FRAMES_PER_VIDEO': 5,
        'UPLOAD_FOLDER': '/tmp/test_uploads'
    }


@pytest.fixture
def sample_video_url():
    """URL de video de ejemplo para tests"""
    return "https://example.com/sample_video.mp4"


@pytest.fixture
def sample_frame_paths(tmp_path):
    """Genera paths de frames de ejemplo"""
    frames = []
    for i in range(3):
        frame_path = tmp_path / f"frame_{i:04d}.jpg"
        frame_path.write_text(f"mock frame {i}")
        frames.append(str(frame_path))
    return frames


@pytest.fixture
def mock_video_analysis():
    """Análisis de video mock para tests"""
    return {
        'detected_products': ['Jarabe de Glucosa', 'Harina de Trigo'],
        'context': 'Preparación de panadería industrial',
        'user_needs': 'Edulcorantes y harinas para producción',
        'suggested_categories': ['Edulcorantes', 'Harinas'],
        'confidence': 0.87
    }


@pytest.fixture
def mock_rag_context():
    """Contexto RAG mock para tests"""
    return """
    Jarabe de Glucosa Premium (SKU: GLUC-001)
    Precio: $25.50/kg
    Categoría: Edulcorantes
    Descripción: Jarabe de glucosa de alta pureza para industria alimentaria.
    
    Harina de Trigo Panadera Tipo 1 (SKU: HARINA-002)
    Precio: $18.00/kg
    Categoría: Harinas
    Descripción: Harina de trigo especial para panadería profesional.
    """
