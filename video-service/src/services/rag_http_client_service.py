"""Servicio para consultar el RAG via HTTP REST API."""

import httpx
import logging
from typing import Dict, Any

from src.utils.config import Config

logger = logging.getLogger(__name__)


class RagHttpClientService:
    """Cliente HTTP para consultar RAG via REST API."""
    
    def __init__(self, rag_url: str = None):
        """
        Inicializa el cliente HTTP para RAG.
        
        Args:
            rag_url: URL base del RAG (default: Config.RAG_API_URL)
        """
        self.rag_url = (rag_url or Config.RAG_API_URL).rstrip('/')
        self.ask_endpoint = f"{self.rag_url}/api/v1/ask"
        logger.info(f"RAG HTTP Client initialized: {self.ask_endpoint}")
    
    async def initialize(self):
        """
        Inicialización (para compatibilidad con interface MCP).
        No hace nada ya que HTTP no requiere setup previo.
        """
        logger.info("✅ RAG HTTP Client ready (no initialization needed)")
        return self
    
    async def query_rag(self, query: str) -> str:
        """
        Consulta el RAG via HTTP POST.
        
        Args:
            query: Pregunta para el RAG
        
        Returns:
            Respuesta del RAG como string
        
        Raises:
            Exception: Si la consulta falla
        """
        try:
            logger.info(f"🔍 Querying RAG via HTTP: {self.ask_endpoint}")
            logger.debug(f"   Query: {query[:100]}...")
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.ask_endpoint,
                    json={
                        "question": query,
                        "top_k": 5,
                        "collection": "medisupply",
                        "force_rebuild": False,
                        "use_query_rewriting": True,
                        "use_reranking": True,
                    },
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                
                result = response.json()
                
                # El RAG devuelve formato: {"answer": "...", "sources": [...]}
                answer = result.get("answer", "")
                
                if not answer:
                    logger.warning("⚠️  RAG returned empty answer")
                    return "No se encontró información en el catálogo."
                
                logger.info(f"✅ RAG response received ({len(answer)} chars)")
                return answer
                
        except httpx.HTTPStatusError as e:
            logger.error(f"❌ RAG HTTP error: {e.response.status_code}")
            raise Exception(f"RAG query failed: HTTP {e.response.status_code}")
        except httpx.TimeoutException:
            logger.error("❌ RAG query timeout")
            raise Exception("RAG query timeout (60s)")
        except Exception as e:
            logger.error(f"❌ RAG query error: {str(e)}")
            raise Exception(f"RAG query failed: {str(e)}")
    
    async def shutdown(self):
        """
        Cleanup (para compatibilidad con interface MCP).
        """
        logger.info("🔌 RAG HTTP Client shutdown")


# Singleton global
_rag_client = None


async def get_rag_client() -> RagHttpClientService:
    """
    Obtiene instancia singleton del cliente RAG HTTP.
    
    Returns:
        Cliente RAG HTTP inicializado
    """
    global _rag_client
    
    if _rag_client is None:
        _rag_client = RagHttpClientService()
        await _rag_client.initialize()
    
    return _rag_client
