import pytest
from unittest.mock import Mock, AsyncMock, patch

from src.services.mcp_client_service import MCPClientService


class TestMCPClientAdditional:
    @pytest.mark.asyncio
    async def test_query_rag_returns_string(self):
        """Test que query_rag retorna string"""
        service = MCPClientService(server_path="/app/mcp_server/rag_server.py")
        
        mock_tool = AsyncMock()
        mock_tool.ainvoke = AsyncMock(return_value="RAG response")
        service.ask_tool = mock_tool
        service._session = Mock()
        
        result = await service.query_rag("test query")
        
        assert isinstance(result, str)
        assert result == "RAG response"
    
    @pytest.mark.asyncio
    async def test_query_rag_with_long_query(self):
        """Test query con texto largo"""
        service = MCPClientService(server_path="/app/mcp_server/rag_server.py")
        
        mock_tool = AsyncMock()
        mock_tool.ainvoke = AsyncMock(return_value="Response")
        service.ask_tool = mock_tool
        service._session = Mock()
        
        long_query = "test " * 100
        result = await service.query_rag(long_query)
        
        assert result == "Response"
        mock_tool.ainvoke.assert_called_once()
    
    def test_initialization_sets_session_to_none(self):
        """Test que session se inicializa como None"""
        service = MCPClientService(server_path="/app/mcp_server/rag_server.py")
        assert service._session is None  # Se inicializa como None
    
    @pytest.mark.asyncio
    async def test_multiple_query_calls(self):
        """Test múltiples llamadas a query_rag"""
        service = MCPClientService(server_path="/app/mcp_server/rag_server.py")
        
        mock_tool = AsyncMock()
        mock_tool.ainvoke = AsyncMock(side_effect=["Response 1", "Response 2"])
        service.ask_tool = mock_tool
        service._session = Mock()
        
        result1 = await service.query_rag("query 1")
        result2 = await service.query_rag("query 2")
        
        assert result1 == "Response 1"
        assert result2 == "Response 2"
        assert mock_tool.ainvoke.call_count == 2
