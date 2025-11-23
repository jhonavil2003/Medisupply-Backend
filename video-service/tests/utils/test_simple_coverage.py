import pytest
from unittest.mock import Mock, patch

from src.services.mcp_client_service import MCPClientService
from src.utils.config import Config


class TestMCPClientCoverage:
    
    def test_mcp_client_has_server_path(self):
        """Test que MCP client almacena server_path"""
        service = MCPClientService(server_path="/app/mcp_server/rag_server.py")
        assert service.server_path == "/app/mcp_server/rag_server.py"
    
    def test_mcp_client_has_lock(self):
        """Test que MCP client tiene lock para concurrencia"""
        service = MCPClientService(server_path="/app/mcp_server/rag_server.py")
        assert service._lock is not None
    
    def test_mcp_client_initializes_with_none_session(self):
        """Test que session empieza como None"""
        service = MCPClientService(server_path="/app/mcp_server/rag_server.py")
        assert service._session is None
        assert service.ask_tool is None


class TestConfigCoverage:
    """Tests simples para Config"""
    
    def test_config_to_dict_exists(self):
        """Test que Config tiene método to_dict"""
        assert hasattr(Config, 'to_dict')
        assert callable(Config.to_dict)
    
    def test_config_to_dict_returns_dict(self):
        """Test que to_dict retorna diccionario"""
        result = Config.to_dict()
        assert isinstance(result, dict)
    
    def test_config_has_aws_settings(self):
        """Test que Config tiene configuración AWS"""
        assert hasattr(Config, 'AWS_REGION')
        assert Config.AWS_REGION is not None
    
    def test_config_has_log_level(self):
        """Test que Config tiene LOG_LEVEL"""
        assert hasattr(Config, 'LOG_LEVEL')
        assert Config.LOG_LEVEL in ['DEBUG', 'INFO', 'WARNING', 'ERROR']
    
    def test_config_has_base_dir(self):
        """Test que Config tiene BASE_DIR"""
        assert hasattr(Config, 'BASE_DIR')
        assert Config.BASE_DIR is not None
    
    def test_config_has_upload_dir(self):
        """Test que Config tiene UPLOAD_DIR"""
        assert hasattr(Config, 'UPLOAD_DIR')
        assert Config.UPLOAD_DIR is not None
    
    def test_config_max_content_length_calculated(self):
        """Test que MAX_CONTENT_LENGTH se calcula correctamente"""
        assert hasattr(Config, 'MAX_CONTENT_LENGTH')
        assert Config.MAX_CONTENT_LENGTH == Config.MAX_VIDEO_SIZE_MB * 1024 * 1024
    
    def test_config_video_download_timeout(self):
        """Test que VIDEO_DOWNLOAD_TIMEOUT está configurado"""
        assert hasattr(Config, 'VIDEO_DOWNLOAD_TIMEOUT')
        assert Config.VIDEO_DOWNLOAD_TIMEOUT > 0
