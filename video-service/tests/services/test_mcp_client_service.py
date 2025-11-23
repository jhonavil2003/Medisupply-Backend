import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.services.mcp_client_service import MCPClientService, get_mcp_client


class TestMCPClientService:
    @pytest.mark.asyncio
    async def test_initialization_creates_session(self):
        """Test que la inicialización crea la sesión MCP"""
        # Arrange
        server_path = "/app/mcp_server/rag_server.py"
        client = MCPClientService(server_path)
        
        # Verificar estado inicial
        assert not client.is_initialized
        assert client._session is None
        assert client.ask_tool is None
    
    @pytest.mark.asyncio
    @patch('src.services.mcp_client_service.stdio_client')
    @patch('src.services.mcp_client_service.ClientSession')
    @patch('src.services.mcp_client_service.load_mcp_tools')
    async def test_initialize_loads_ask_tool(
        self,
        mock_load_tools,
        mock_session_class,
        mock_stdio_client
    ):
        """Test que initialize carga correctamente la herramienta 'ask'"""
        # Arrange
        client = MCPClientService("/app/mcp_server/rag_server.py")
        
        # Mock stdio_client
        mock_stdio_ctx = AsyncMock()
        mock_stdio_ctx.__aenter__.return_value = (Mock(), Mock())
        mock_stdio_client.return_value = mock_stdio_ctx
        
        # Mock ClientSession
        mock_session = AsyncMock()
        mock_session.initialize = AsyncMock()
        mock_session_ctx = AsyncMock()
        mock_session_ctx.__aenter__.return_value = mock_session
        mock_session_class.return_value = mock_session_ctx
        
        # Mock tools
        mock_ask_tool = Mock()
        mock_ask_tool.name = "ask"
        mock_load_tools.return_value = [mock_ask_tool]
        
        # Act
        await client.initialize()
        
        # Assert
        assert client.is_initialized
        assert client._session is not None
        assert client.ask_tool is not None
        mock_load_tools.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('src.services.mcp_client_service.stdio_client')
    @patch('src.services.mcp_client_service.ClientSession')
    @patch('src.services.mcp_client_service.load_mcp_tools')
    async def test_initialize_raises_if_no_ask_tool(
        self,
        mock_load_tools,
        mock_session_class,
        mock_stdio_client
    ):
        """Test que initialize lanza error si no encuentra 'ask' tool"""
        # Arrange
        client = MCPClientService("/app/mcp_server/rag_server.py")
        
        # Mock stdio y session
        mock_stdio_ctx = AsyncMock()
        mock_stdio_ctx.__aenter__.return_value = (Mock(), Mock())
        mock_stdio_client.return_value = mock_stdio_ctx
        
        mock_session = AsyncMock()
        mock_session.initialize = AsyncMock()
        mock_session_ctx = AsyncMock()
        mock_session_ctx.__aenter__.return_value = mock_session
        mock_session_class.return_value = mock_session_ctx
        
        # Mock tools sin 'ask'
        mock_other_tool = Mock()
        mock_other_tool.name = "other_tool"
        mock_load_tools.return_value = [mock_other_tool]
        
        # Act & Assert
        with pytest.raises(ValueError, match="does not have 'ask' tool"):
            await client.initialize()
    
    @pytest.mark.asyncio
    async def test_query_rag_without_initialization_initializes_first(self):
        """Test que query_rag inicializa si no está inicializado"""
        # Arrange
        client = MCPClientService("/app/mcp_server/rag_server.py")
        client.initialize = AsyncMock()
        
        mock_tool = AsyncMock()
        mock_tool.ainvoke = AsyncMock(return_value="Mock RAG response")
        client.ask_tool = mock_tool
        client._session = Mock()  # Simular sesión inicializada
        
        # Act
        result = await client.query_rag("test query")
        
        # Assert
        assert result == "Mock RAG response"
        mock_tool.ainvoke.assert_called_once_with({"query": "test query"})
    
    @pytest.mark.asyncio
    async def test_shutdown_cleans_resources(self):
        """Test que shutdown limpia todos los recursos"""
        # Arrange
        client = MCPClientService("/app/mcp_server/rag_server.py")
        
        # Simular sesión inicializada
        mock_session = AsyncMock()
        mock_session.__aexit__ = AsyncMock()
        client._session = mock_session
        
        mock_stdio = AsyncMock()
        mock_stdio.__aexit__ = AsyncMock()
        client._stdio_ctx = mock_stdio
        
        client.ask_tool = Mock()
        
        # Act
        await client.shutdown()
        
        # Assert
        assert client._session is None
        assert client._stdio_ctx is None
        assert client.ask_tool is None
        assert not client.is_initialized
