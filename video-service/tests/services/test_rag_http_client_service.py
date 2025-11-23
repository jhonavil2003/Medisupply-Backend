import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.services.rag_http_client_service import RagHttpClientService


class TestRagHttpClientService:
    
    def test_initialization_default_url(self):
        """Test inicialización con URL por defecto"""
        service = RagHttpClientService()
        assert "8001" in service.rag_url or "ask" in service.ask_endpoint
    
    def test_initialization_custom_url(self):
        """Test inicialización con URL personalizada"""
        custom_url = "http://custom-rag.com:9000"
        service = RagHttpClientService(rag_url=custom_url)
        assert service.rag_url == custom_url
        assert service.ask_endpoint == f"{custom_url}/api/v1/ask"
    
    def test_initialization_strips_trailing_slash(self):
        """Test que elimina slash final de la URL"""
        service = RagHttpClientService(rag_url="http://example.com/")
        assert service.rag_url == "http://example.com"
    
    @pytest.mark.asyncio
    async def test_initialize_returns_self(self):
        """Test que initialize retorna self"""
        service = RagHttpClientService()
        result = await service.initialize()
        assert result is service
    
    @pytest.mark.asyncio
    @patch('src.services.rag_http_client_service.httpx.AsyncClient')
    async def test_query_rag_success(self, mock_client_class):
        """Test consulta exitosa al RAG"""
        # Arrange
        service = RagHttpClientService()
        
        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "answer": "Product recommendation based on query"
        }
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # Act
        result = await service.query_rag("What products do you recommend?")
        
        # Assert
        assert "Product recommendation" in result
        mock_client.post.assert_called_once()
        call_kwargs = mock_client.post.call_args[1]
        assert call_kwargs['json']['question'] == "What products do you recommend?"
    
    @pytest.mark.asyncio
    @patch('src.services.rag_http_client_service.httpx.AsyncClient')
    async def test_query_rag_http_error(self, mock_client_class):
        """Test manejo de error HTTP"""
        service = RagHttpClientService()
        
        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = Exception("Server Error")
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        with pytest.raises(Exception):
            await service.query_rag("test query")
    
    @pytest.mark.asyncio
    @patch('src.services.rag_http_client_service.httpx.AsyncClient')
    async def test_query_rag_timeout(self, mock_client_class):
        """Test manejo de timeout"""
        service = RagHttpClientService()
        
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=TimeoutError("Request timeout"))
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        with pytest.raises(Exception):
            await service.query_rag("test query")
    
    @pytest.mark.asyncio
    @patch('src.services.rag_http_client_service.httpx.AsyncClient')
    async def test_query_rag_empty_response(self, mock_client_class):
        """Test respuesta vacía del RAG"""
        service = RagHttpClientService()
        
        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        result = await service.query_rag("test")
        assert result == "No se encontró información en el catálogo."
    
    @pytest.mark.asyncio
    async def test_shutdown_does_nothing(self):
        """Test que shutdown no hace nada (HTTP es stateless)"""
        service = RagHttpClientService()
        # No debe lanzar excepciones
        await service.shutdown()
