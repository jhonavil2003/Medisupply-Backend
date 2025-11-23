import pytest
from unittest.mock import Mock, AsyncMock, patch

from src.services.rag_http_client_service import RagHttpClientService


class TestRagHttpClientAdditional:
    
    def test_initialization_formats_url(self):
        """Test que inicialización formatea URL"""
        service = RagHttpClientService("http://localhost:8001")
        assert service.rag_url == "http://localhost:8001"
        assert "/api/v1/ask" in service.ask_endpoint
    
    def test_initialization_with_default_url(self):
        """Test inicialización con URL por defecto"""
        with patch('src.services.rag_http_client_service.Config') as mock_config:
            mock_config.RAG_API_URL = "http://default:8001"
            service = RagHttpClientService()
            assert "http://default:8001" in service.rag_url
    
    @pytest.mark.asyncio
    async def test_query_rag_with_special_characters(self):
        """Test query con caracteres especiales"""
        service = RagHttpClientService()
        
        with patch('src.services.rag_http_client_service.httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"answer": "Response with special chars: áéíóú"}
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            result = await service.query_rag("query with áéíóú")
            
            assert "special chars" in result
    
    @pytest.mark.asyncio
    async def test_query_rag_logs_request(self):
        """Test que query_rag hace logging"""
        service = RagHttpClientService()
        
        with patch('src.services.rag_http_client_service.httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"answer": "Response"}
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            with patch('src.services.rag_http_client_service.logger') as mock_logger:
                await service.query_rag("test")
                assert mock_logger.info.called
    
    @pytest.mark.asyncio
    async def test_initialize_returns_self(self):
        """Test que initialize retorna self"""
        service = RagHttpClientService()
        result = await service.initialize()
        assert result is service
    
    @pytest.mark.asyncio
    async def test_shutdown_completes(self):
        """Test que shutdown se completa sin error"""
        service = RagHttpClientService()
        await service.shutdown()  # No debe lanzar excepción
    
    def test_url_stripping_multiple_slashes(self):
        """Test que remueve múltiples slashes finales"""
        service = RagHttpClientService("http://localhost:8001///")
        assert not service.rag_url.endswith("/")
