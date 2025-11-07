"""
Sistema de Eventos de Inventario.

Este módulo define los eventos que se disparan cuando el inventario cambia
y los helpers para detectar cambios significativos.
"""

from typing import Dict, Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class InventoryChangeType:
    """Tipos de cambios de inventario."""
    UPDATE = 'update'                    # Actualización general
    LOW_STOCK = 'low_stock'              # Stock bajo
    OUT_OF_STOCK = 'out_of_stock'        # Producto agotado
    RESTOCK = 'restock'                  # Reabastecimiento
    RESERVATION = 'reservation'          # Reserva de stock
    RESERVATION_RELEASED = 'reservation_released'  # Liberación de reserva
    SALE = 'sale'                        # Venta
    ADJUSTMENT = 'adjustment'            # Ajuste manual


class InventoryEvent:
    """
    Representa un evento de cambio de inventario.
    """
    
    def __init__(
        self,
        product_sku: str,
        change_type: str,
        previous_quantity: int,
        new_quantity: int,
        distribution_center_id: Optional[int] = None,
        distribution_center_code: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        self.product_sku = product_sku.upper()
        self.change_type = change_type
        self.previous_quantity = previous_quantity
        self.new_quantity = new_quantity
        self.quantity_change = new_quantity - previous_quantity
        self.distribution_center_id = distribution_center_id
        self.distribution_center_code = distribution_center_code
        self.timestamp = datetime.utcnow()
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict:
        """Convierte el evento a diccionario para serialización."""
        return {
            'product_sku': self.product_sku,
            'change_type': self.change_type,
            'previous_quantity': self.previous_quantity,
            'new_quantity': self.new_quantity,
            'quantity_change': self.quantity_change,
            'distribution_center_id': self.distribution_center_id,
            'distribution_center_code': self.distribution_center_code,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata
        }
    
    def is_significant_change(self, threshold_percentage: float = 10.0) -> bool:
        """
        Determina si el cambio es significativo.
        
        Args:
            threshold_percentage: Porcentaje mínimo de cambio para considerar significativo
        
        Returns:
            True si el cambio es significativo
        """
        if self.previous_quantity == 0:
            return True  # Cualquier cambio desde 0 es significativo
        
        change_percentage = abs(self.quantity_change / self.previous_quantity) * 100
        return change_percentage >= threshold_percentage


class InventoryEventDetector:
    """
    Detecta y clasifica cambios de inventario.
    """
    
    @staticmethod
    def detect_change_type(
        previous_quantity: int,
        new_quantity: int,
        minimum_stock_level: int = 0,
        reorder_point: Optional[int] = None
    ) -> str:
        """
        Detecta el tipo de cambio basado en las cantidades.
        
        Args:
            previous_quantity: Cantidad anterior
            new_quantity: Cantidad nueva
            minimum_stock_level: Nivel mínimo de stock
            reorder_point: Punto de reorden
        
        Returns:
            Tipo de cambio (InventoryChangeType)
        """
        # Producto agotado
        if new_quantity == 0 and previous_quantity > 0:
            return InventoryChangeType.OUT_OF_STOCK
        
        # Reabastecimiento (de 0 a algo)
        if previous_quantity == 0 and new_quantity > 0:
            return InventoryChangeType.RESTOCK
        
        # Stock bajo (cruzó el punto de reorden)
        if reorder_point and previous_quantity > reorder_point >= new_quantity > 0:
            return InventoryChangeType.LOW_STOCK
        
        # Stock bajo (por debajo del mínimo)
        if minimum_stock_level > 0 and new_quantity <= minimum_stock_level and previous_quantity > minimum_stock_level:
            return InventoryChangeType.LOW_STOCK
        
        # Venta (disminución)
        if new_quantity < previous_quantity:
            return InventoryChangeType.SALE
        
        # Reabastecimiento (incremento significativo)
        if new_quantity > previous_quantity:
            increase_percentage = ((new_quantity - previous_quantity) / previous_quantity) * 100
            if increase_percentage > 20:  # Incremento mayor al 20%
                return InventoryChangeType.RESTOCK
        
        # Actualización general
        return InventoryChangeType.UPDATE
    
    @staticmethod
    def should_notify(
        previous_quantity: int,
        new_quantity: int,
        minimum_threshold_percentage: float = 5.0
    ) -> bool:
        """
        Determina si se debe notificar el cambio.
        
        Args:
            previous_quantity: Cantidad anterior
            new_quantity: Cantidad nueva
            minimum_threshold_percentage: Porcentaje mínimo de cambio para notificar
        
        Returns:
            True si se debe notificar
        """
        # Siempre notificar cambios a/desde 0
        if previous_quantity == 0 or new_quantity == 0:
            return True
        
        # Notificar si el cambio es significativo
        change_percentage = abs((new_quantity - previous_quantity) / previous_quantity) * 100
        return change_percentage >= minimum_threshold_percentage
    
    @staticmethod
    def create_event(
        product_sku: str,
        previous_quantity: int,
        new_quantity: int,
        distribution_center_id: Optional[int] = None,
        distribution_center_code: Optional[str] = None,
        minimum_stock_level: int = 0,
        reorder_point: Optional[int] = None,
        metadata: Optional[Dict] = None
    ) -> InventoryEvent:
        """
        Crea un evento de inventario detectando automáticamente el tipo.
        
        Args:
            product_sku: SKU del producto
            previous_quantity: Cantidad anterior
            new_quantity: Cantidad nueva
            distribution_center_id: ID del centro de distribución
            distribution_center_code: Código del centro de distribución
            minimum_stock_level: Nivel mínimo de stock
            reorder_point: Punto de reorden
            metadata: Metadatos adicionales
        
        Returns:
            InventoryEvent
        """
        change_type = InventoryEventDetector.detect_change_type(
            previous_quantity,
            new_quantity,
            minimum_stock_level,
            reorder_point
        )
        
        return InventoryEvent(
            product_sku=product_sku,
            change_type=change_type,
            previous_quantity=previous_quantity,
            new_quantity=new_quantity,
            distribution_center_id=distribution_center_id,
            distribution_center_code=distribution_center_code,
            metadata=metadata
        )


class InventoryEventPublisher:
    """
    Publica eventos de inventario a través de WebSockets.
    """
    
    @staticmethod
    def publish(event: InventoryEvent):
        """
        Publica un evento de inventario.
        
        Args:
            event: InventoryEvent a publicar
        """
        from src.websockets.websocket_manager import InventoryNotifier
        from src.commands.get_stock_levels import GetStockLevels
        
        try:
            # ✅ Obtener información actualizada del stock de TODOS los centros
            stock_command = GetStockLevels(
                product_sku=event.product_sku,
                # ✅ NO pasar distribution_center_id para obtener todos los centros
            )
            stock_result = stock_command.execute()
            
            # Preparar datos del stock
            stock_data = {
                'product_sku': event.product_sku,
                'total_available': stock_result.get('total_available', 0),
                'total_reserved': stock_result.get('total_reserved', 0),
                'total_in_transit': stock_result.get('total_in_transit', 0),
                'distribution_centers': stock_result.get('distribution_centers', []),
                'quantity_change': event.quantity_change,
                'previous_quantity': event.previous_quantity,
                'new_quantity': event.new_quantity,
                # ✅ Agregar el centro que se actualizó para referencia
                'updated_center_id': event.distribution_center_id,
                'updated_center_code': event.distribution_center_code
            }
            
            # Enviar notificación
            InventoryNotifier.notify_stock_change(
                product_sku=event.product_sku,
                stock_data=stock_data,
                change_type=event.change_type
            )
            
            logger.info(
                f"📢 Evento publicado: {event.product_sku} - "
                f"{event.change_type} ({event.previous_quantity} → {event.new_quantity})"
            )
            
        except Exception as e:
            logger.error(f"❌ Error publicando evento: {str(e)}")
    
    @staticmethod
    def publish_batch(events: List[InventoryEvent]):
        """
        Publica múltiples eventos en batch.
        
        Args:
            events: Lista de InventoryEvents
        """
        for event in events:
            InventoryEventPublisher.publish(event)


def track_inventory_change(
    product_sku: str,
    previous_quantity: int,
    new_quantity: int,
    distribution_center_id: Optional[int] = None,
    distribution_center_code: Optional[str] = None,
    minimum_stock_level: int = 0,
    reorder_point: Optional[int] = None,
    metadata: Optional[Dict] = None,
    auto_publish: bool = True
) -> Optional[InventoryEvent]:
    """
    Helper function para rastrear y opcionalmente publicar cambios de inventario.
    
    Args:
        product_sku: SKU del producto
        previous_quantity: Cantidad anterior
        new_quantity: Cantidad nueva
        distribution_center_id: ID del centro de distribución
        distribution_center_code: Código del centro de distribución
        minimum_stock_level: Nivel mínimo de stock
        reorder_point: Punto de reorden
        metadata: Metadatos adicionales
        auto_publish: Si True, publica automáticamente el evento
    
    Returns:
        InventoryEvent si el cambio es significativo, None si no
    """
    # Verificar si el cambio es significativo
    should_notify = InventoryEventDetector.should_notify(
        previous_quantity,
        new_quantity
    )
    
    if not should_notify:
        logger.debug(f"Cambio no significativo para {product_sku}, no se notifica")
        return None
    
    # Crear evento
    event = InventoryEventDetector.create_event(
        product_sku=product_sku,
        previous_quantity=previous_quantity,
        new_quantity=new_quantity,
        distribution_center_id=distribution_center_id,
        distribution_center_code=distribution_center_code,
        minimum_stock_level=minimum_stock_level,
        reorder_point=reorder_point,
        metadata=metadata
    )
    
    # Publicar si está habilitado
    if auto_publish:
        InventoryEventPublisher.publish(event)
    
    return event
