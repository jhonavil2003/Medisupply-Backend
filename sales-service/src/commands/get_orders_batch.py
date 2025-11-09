"""
Comando para obtener múltiples órdenes por sus IDs.

Este comando permite recuperar un conjunto de órdenes en una sola operación,
optimizando la comunicación entre microservicios.
"""

from typing import List, Dict, Any
from src.models.order import Order
from src.session import db
import logging

logger = logging.getLogger(__name__)


class GetOrdersBatch:
    """
    Comando para obtener múltiples órdenes por sus IDs.
    
    Retorna los detalles completos de las órdenes encontradas,
    junto con una lista de IDs no encontrados.
    """
    
    def __init__(self, order_ids: List[int]):
        """
        Inicializa el comando.
        
        Args:
            order_ids: Lista de IDs de órdenes a recuperar
        """
        self.order_ids = order_ids if order_ids else []
    
    def execute(self) -> Dict[str, Any]:
        """
        Ejecuta el comando para recuperar las órdenes.
        
        Returns:
            Dict con:
            {
                'orders': List[Dict],        # Órdenes encontradas con detalles completos
                'total': int,                 # Número de órdenes encontradas
                'not_found': List[int],       # IDs de órdenes no encontradas
                'requested': int              # Número de IDs solicitados
            }
        """
        if not self.order_ids:
            logger.warning("GetOrdersBatch called with empty order_ids list")
            return {
                'orders': [],
                'total': 0,
                'not_found': [],
                'requested': 0
            }
        
        # Eliminar duplicados manteniendo el orden
        unique_order_ids = list(dict.fromkeys(self.order_ids))
        
        logger.info(f"Fetching batch of {len(unique_order_ids)} orders")
        
        # Consultar todas las órdenes en una sola query
        orders = db.session.query(Order).filter(
            Order.id.in_(unique_order_ids)
        ).all()
        
        # Convertir a diccionario con detalles completos
        orders_dict = [
            order.to_dict(include_items=True, include_customer=True)
            for order in orders
        ]
        
        # Identificar IDs encontrados
        found_ids = {order.id for order in orders}
        
        # Identificar IDs no encontrados
        not_found_ids = [
            order_id for order_id in unique_order_ids
            if order_id not in found_ids
        ]
        
        if not_found_ids:
            logger.warning(f"Orders not found: {not_found_ids}")
        
        logger.info(
            f"Batch retrieval complete: {len(orders_dict)} found, "
            f"{len(not_found_ids)} not found"
        )
        
        return {
            'orders': orders_dict,
            'total': len(orders_dict),
            'not_found': not_found_ids,
            'requested': len(unique_order_ids)
        }
