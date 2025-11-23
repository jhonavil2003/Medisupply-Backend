"""
MCP Client Service
==================

Servicio para gestionar conexión MCP con el servidor RAG.
CLONADO desde RagAgentService del proyecto de agentes.

Este servicio implementa el patrón EXACTO usado en el sistema de agentes
para conectarse al servidor MCP del RAG via stdio protocol.

Diferencias con el Agente:
- NO usa LangGraph (eliminado)
- NO construye workflow (eliminado)
- SÍ mantiene la lógica de inicialización MCP
- SÍ expone método directo para consultar RAG
"""

from mcp.client.stdio import stdio_client
from mcp import ClientSession, StdioServerParameters
from langchain_mcp_adapters.tools import load_mcp_tools
import asyncio
import logging
import sys

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


class MCPClientService:
    """
    Servicio para gestionar conexión MCP con el servidor RAG.
    
    Este servicio replica el patrón de RagAgentService pero simplificado
    para uso directo desde Flask (sin LangGraph).
    
    Responsabilidades:
    - Inicializar sesión MCP con el servidor RAG
    - Cargar herramienta 'ask' del servidor MCP
    - Proveer método async para consultar RAG
    - Gestionar ciclo de vida de la sesión
    
    Uso:
        client = MCPClientService(server_path="/app/mcp_server/rag_server.py")
        await client.initialize()
        result = await client.query_rag("¿Qué productos de glucosa tienen?")
        await client.shutdown()
    """
    
    def __init__(self, server_path: str):
        """
        Inicializa el servicio MCP.
        
        Args:
            server_path: Path absoluto al script del servidor MCP (rag_server.py)
        """
        self.server_path = server_path
        self._lock = asyncio.Lock()
        self._stdio_ctx = None
        self._session = None
        self.ask_tool = None
        
        logger.info(f"MCPClientService initialized with server: {server_path}")
    
    async def initialize(self):
        """
        Inicializa sesión MCP y carga herramienta 'ask'.
        
        PATRÓN CLONADO del Agente actual (RagAgentService.initialize).
        
        Flujo:
        1. Crear parámetros del servidor (comando + args)
        2. Iniciar cliente stdio
        3. Crear sesión de comunicación
        4. Realizar handshake con servidor
        5. Cargar herramientas disponibles
        6. Extraer herramienta 'ask'
        
        Raises:
            ValueError: Si el servidor no expone la herramienta 'ask'
            Exception: Si hay errores de conexión o timeout
        """
        async with self._lock:
            if self._session is not None:
                logger.info("MCP session already initialized, skipping...")
                return
            
            try:
                logger.info("🔄 Starting MCP client initialization...")
                
                # ===== PASO 1: Crear parámetros del servidor =====
                # Usar 'uv' como comando (gestor de entornos Python)
                server_params = StdioServerParameters(
                    command="uv",
                    args=["run", self.server_path]
                )
                logger.info(f"   Server params: uv run {self.server_path}")
                
                # ===== PASO 2: Iniciar cliente stdio =====
                logger.info("   Initializing stdio_client...")
                self._stdio_ctx = stdio_client(server_params)
                read, write = await self._stdio_ctx.__aenter__()
                logger.info("   ✓ stdio_client context entered")
                
                # ===== PASO 3: Crear sesión =====
                logger.info("   Creating MCP session...")
                self._session = await ClientSession(read, write).__aenter__()
                logger.info("   ✓ ClientSession context entered")
                
                # ===== PASO 4: Realizar handshake =====
                logger.info("   Performing MCP handshake...")
                await self._session.initialize()
                logger.info("   ✓ MCP session initialized successfully")
                
                # ===== PASO 5: Cargar herramientas =====
                logger.info("   Loading MCP tools...")
                tools = await load_mcp_tools(self._session)
                logger.info(f"   ✓ Loaded {len(tools)} tools from MCP server")
                
                # Crear diccionario indexado por nombre
                tools_by_name = {tool.name: tool for tool in tools}
                logger.info(f"   Available tools: {list(tools_by_name.keys())}")
                
                # ===== PASO 6: Extraer herramienta 'ask' =====
                if "ask" not in tools_by_name:
                    available_tools = ', '.join(tools_by_name.keys())
                    raise ValueError(
                        f"MCP server does not have 'ask' tool. "
                        f"Available tools: {available_tools}"
                    )
                
                self.ask_tool = tools_by_name["ask"]
                logger.info("   ✓ Tool 'ask' extracted successfully")
                
                logger.info("✅ MCP Client initialized and ready")
                
            except Exception as e:
                logger.error(f"❌ Error initializing MCP client: {str(e)}")
                # Cleanup en caso de error
                await self._cleanup_on_error()
                raise
    
    async def query_rag(self, query: str) -> str:
        """
        Consulta el RAG vía MCP.
        
        PATRÓN CLONADO del Agente (ask_node en rag_agent.py).
        Invoca la herramienta MCP 'ask' con el query del usuario.
        
        Args:
            query: Pregunta sobre productos o información del catálogo
        
        Returns:
            Contexto recuperado del RAG como string
        
        Raises:
            ValueError: Si la sesión no está inicializada
            Exception: Si hay errores durante la invocación
        
        Example:
            >>> result = await client.query_rag("¿Tienen jarabe de glucosa?")
            >>> print(result)  # "Sí, tenemos Jarabe de Glucosa Premium..."
        """
        # Verificar que la sesión esté inicializada
        if self._session is None or self.ask_tool is None:
            logger.warning("MCP session not initialized, initializing now...")
            await self.initialize()
        
        logger.info(f"🔍 Querying RAG via MCP: '{query[:100]}...'")
        
        try:
            # ===== INVOCACIÓN EXACTA DEL PATRÓN DEL AGENTE =====
            # ask_node.tool.ainvoke({"query": question})
            result = await self.ask_tool.ainvoke({"query": query})
            
            logger.info(f"✅ RAG query completed (result length: {len(result)} chars)")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error querying RAG via MCP: {str(e)}")
            raise
    
    async def shutdown(self):
        """
        Cierra sesión MCP y limpia recursos.
        
        PATRÓN CLONADO del Agente (RagAgentService.shutdown).
        
        Debe llamarse siempre al finalizar para liberar recursos:
        - Cierra la sesión MCP
        - Cierra el contexto stdio
        - Resetea variables internas
        """
        async with self._lock:
            logger.info("🔄 Shutting down MCP client...")
            
            if self._session:
                try:
                    await self._session.__aexit__(None, None, None)
                    logger.info("   ✓ MCP session closed")
                except Exception as e:
                    logger.error(f"   ⚠️ Error closing session: {e}")
                finally:
                    self._session = None
            
            if self._stdio_ctx:
                try:
                    await self._stdio_ctx.__aexit__(None, None, None)
                    logger.info("   ✓ stdio_client context closed")
                except Exception as e:
                    logger.error(f"   ⚠️ Error closing stdio: {e}")
                finally:
                    self._stdio_ctx = None
            
            self.ask_tool = None
            logger.info("✅ MCP client shutdown complete")
    
    async def _cleanup_on_error(self):
        """Limpieza en caso de error durante inicialización"""
        if self._session:
            try:
                await self._session.__aexit__(None, None, None)
            except:
                pass
            self._session = None
        
        if self._stdio_ctx:
            try:
                await self._stdio_ctx.__aexit__(None, None, None)
            except:
                pass
            self._stdio_ctx = None
        
        self.ask_tool = None
    
    @property
    def is_initialized(self) -> bool:
        """Verifica si el cliente está inicializado y listo"""
        return (
            self._session is not None and
            self.ask_tool is not None
        )
    
    def __repr__(self):
        status = "initialized" if self.is_initialized else "not initialized"
        return f"<MCPClientService(server={self.server_path}, status={status})>"


# ========== SINGLETON INSTANCE ==========
# Instancia global para reutilización en toda la app
_mcp_client_instance = None


async def get_mcp_client(server_path: str = None) -> MCPClientService:
    """
    Obtiene instancia singleton del MCP Client.
    
    Args:
        server_path: Path al servidor MCP (solo necesario en primera llamada)
    
    Returns:
        Instancia inicializada de MCPClientService
    """
    global _mcp_client_instance
    
    if _mcp_client_instance is None:
        if server_path is None:
            from src.utils.config import Config
            server_path = Config.RAG_MCP_SERVER_PATH
        
        _mcp_client_instance = MCPClientService(server_path)
        await _mcp_client_instance.initialize()
    
    return _mcp_client_instance


async def shutdown_mcp_client():
    """Cierra la instancia singleton del MCP Client"""
    global _mcp_client_instance
    
    if _mcp_client_instance is not None:
        await _mcp_client_instance.shutdown()
        _mcp_client_instance = None
