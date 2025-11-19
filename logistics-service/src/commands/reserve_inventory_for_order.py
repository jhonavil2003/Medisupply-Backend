"""
Comando para reservar inventario cuando se crea una orden.

Este comando actualiza inventory.quantity_reserved para reflejar
que los productos están comprometidos con una orden confirmada.

Diferencia con cart_reservations:
- cart_reservations: Reservas temporales (15 min) mientras el usuario navega
- inventory.quantity_reserved: Reservas permanentes de órdenes confirmadas

Flujo:
1. Orden creada → Reservar inventario (quantity_reserved += quantity)
2. Orden despachada → Reducir quantity_available
3. Orden cancelada → Liberar reserva (quantity_reserved -= quantity)
"""

from datetime import datetime
from typing import List, Dict, Optional
from sqlalchemy import and_
from src.session import db
from src.models.inventory import Inventory
from src.errors.errors import ValidationError, NotFoundError, ConflictError
from src.websockets.inventory_events import InventoryChangeType
import logging

logger = logging.getLogger(__name__)


class ReserveInventoryForOrder:
    """
    Comando para reservar inventario al crear una orden.
    
    Actualiza quantity_reserved en la tabla inventory para todos
    los items de una orden en una transacción atómica.
    """
    
    def __init__(self, order_id: str, items: List[Dict]):
        """
        Args:
            order_id: ID de la orden
            items: Lista de items con formato:
                [
                    {
                        "product_sku": "JER-001",
                        "quantity": 5,
                        "distribution_center_id": 1
                    },
                    ...
                ]
        """
        self.order_id = order_id
        self.items = items
        self.reserved_items = []  # Para tracking
    
    def execute(self) -> Dict:
        """
        Ejecuta la reserva de inventario para todos los items de la orden.
        
        Returns:
            {
                "success": True,
                "order_id": "ORD-2025-001",
                "items_reserved": [
                    {
                        "product_sku": "JER-001",
                        "quantity_reserved": 5,
                        "distribution_center_id": 1,
                        "quantity_reserved_total": 150  # Después de la reserva
                    },
                    ...
                ]
            }
        """
        # Validar parámetros
        self._validate_parameters()
        
        try:
            # Reservar cada item (dentro de la misma transacción)
            for item in self.items:
                self._reserve_item(item)
            
            # Commit de la transacción completa
            db.session.commit()
            
            # Emitir eventos WebSocket para cada item
            for reserved_item in self.reserved_items:
                self._emit_websocket_event(reserved_item)
            
            logger.info(
                f"✅ Inventario reservado para orden {self.order_id}: "
                f"{len(self.reserved_items)} items"
            )
            
            return {
                'success': True,
                'order_id': self.order_id,
                'items_reserved': self.reserved_items,
                'message': f'Inventario reservado exitosamente para {len(self.reserved_items)} items'
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Error reservando inventario para orden {self.order_id}: {str(e)}")
            raise
    
    def _validate_parameters(self):
        """Valida los parámetros de entrada."""
        if not self.order_id:
            raise ValidationError("order_id es requerido")
        
        if not self.items or not isinstance(self.items, list):
            raise ValidationError("items debe ser una lista no vacía")
        
        if len(self.items) == 0:
            raise ValidationError("La orden debe tener al menos un item")
        
        # Validar cada item
        for idx, item in enumerate(self.items):
            if not isinstance(item, dict):
                raise ValidationError(f"Item {idx} debe ser un diccionario")
            
            if 'product_sku' not in item:
                raise ValidationError(f"Item {idx}: product_sku es requerido")
            
            if 'quantity' not in item:
                raise ValidationError(f"Item {idx}: quantity es requerido")
            
            if not isinstance(item['quantity'], (int, float)) or item['quantity'] <= 0:
                raise ValidationError(
                    f"Item {idx}: quantity debe ser un número positivo"
                )
            
            if 'distribution_center_id' not in item:
                raise ValidationError(f"Item {idx}: distribution_center_id es requerido")
    
    def _reserve_item(self, item: Dict):
        """
        Reserva inventario para un item específico.
        
        Args:
            item: {"product_sku": "JER-001", "quantity": 5, "distribution_center_id": 1}
        """
        product_sku = item['product_sku'].upper()
        quantity = int(item['quantity'])
        distribution_center_id = item['distribution_center_id']
        
        # Buscar inventario
        inventory = Inventory.query.filter(
            and_(
                Inventory.product_sku == product_sku,
                Inventory.distribution_center_id == distribution_center_id
            )
        ).first()
        
        if not inventory:
            raise NotFoundError(
                f"No se encontró inventario para {product_sku} "
                f"en centro de distribución {distribution_center_id}"
            )
        
        # Validar que hay suficiente stock disponible
        # quantity_available debe ser suficiente para la reserva
        if inventory.quantity_available < quantity:
            raise ConflictError(
                f"Stock insuficiente para {product_sku}. "
                f"Disponible: {inventory.quantity_available}, "
                f"Solicitado: {quantity}"
            )
        
        # Actualizar quantity_reserved
        old_quantity_reserved = inventory.quantity_reserved
        inventory.quantity_reserved += quantity
        inventory.last_movement_date = datetime.utcnow()
        
        # Tracking para response y WebSocket
        reserved_item = {
            'product_sku': product_sku,
            'quantity_reserved': quantity,
            'distribution_center_id': distribution_center_id,
            'quantity_reserved_before': old_quantity_reserved,
            'quantity_reserved_after': inventory.quantity_reserved,
            'quantity_available': inventory.quantity_available
        }
        
        self.reserved_items.append(reserved_item)
        
        logger.info(
            f"📦 Reservando inventario: {product_sku} - "
            f"Cantidad: {quantity} - "
            f"Reserved antes: {old_quantity_reserved} → después: {inventory.quantity_reserved}"
        )
    
    def _emit_websocket_event(self, reserved_item: Dict):
        """Emite evento WebSocket de reserva de inventario."""
        try:
            from src.websockets.websocket_manager import InventoryNotifier
            from src.commands.get_stock_levels import GetStockLevels
            
            # Obtener stock actualizado (con el cálculo correcto de disponible)
            stock_command = GetStockLevels(
                product_sku=reserved_item['product_sku'],
                include_reserved=True,
                include_in_transit=False
            )
            stock_data = stock_command.execute()
            
            # Emitir notificación WebSocket
            InventoryNotifier.notify_stock_change(
                product_sku=reserved_item['product_sku'],
                stock_data=stock_data,
                change_type=InventoryChangeType.RESERVATION
            )
            
            logger.info(
                f"📡 WebSocket: Notificado cambio de stock para {reserved_item['product_sku']} "
                f"(disponible: {stock_data.get('total_available')})"
            )
        except Exception as e:
            # No fallar si el WebSocket falla
            logger.warning(f"⚠️ Error emitiendo evento WebSocket: {str(e)}")


class ReleaseInventoryForOrder:
    """
    Comando para liberar inventario cuando se cancela una orden.
    
    Reduce quantity_reserved para devolver el stock al pool disponible.
    """
    
    def __init__(self, order_id: str, items: List[Dict]):
        """
        Args:
            order_id: ID de la orden
            items: Lista de items con formato:
                [
                    {
                        "product_sku": "JER-001",
                        "quantity": 5,
                        "distribution_center_id": 1
                    },
                    ...
                ]
        """
        self.order_id = order_id
        self.items = items
        self.released_items = []
    
    def execute(self) -> Dict:
        """
        Libera inventario reservado por una orden cancelada.
        
        Returns:
            {
                "success": True,
                "order_id": "ORD-2025-001",
                "items_released": [...]
            }
        """
        self._validate_parameters()
        
        try:
            for item in self.items:
                self._release_item(item)
            
            db.session.commit()
            
            # Emitir eventos WebSocket
            for released_item in self.released_items:
                self._emit_websocket_event(released_item)
            
            logger.info(
                f"✅ Inventario liberado para orden {self.order_id}: "
                f"{len(self.released_items)} items"
            )
            
            return {
                'success': True,
                'order_id': self.order_id,
                'items_released': self.released_items,
                'message': f'Inventario liberado exitosamente para {len(self.released_items)} items'
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Error liberando inventario para orden {self.order_id}: {str(e)}")
            raise
    
    def _validate_parameters(self):
        """Valida los parámetros de entrada."""
        if not self.order_id:
            raise ValidationError("order_id es requerido")
        
        if not self.items or not isinstance(self.items, list):
            raise ValidationError("items debe ser una lista no vacía")
        
        if len(self.items) == 0:
            raise ValidationError("La orden debe tener al menos un item")
    
    def _release_item(self, item: Dict):
        """Libera inventario para un item específico."""
        product_sku = item['product_sku'].upper()
        quantity = int(item['quantity'])
        distribution_center_id = item['distribution_center_id']
        
        # Buscar inventario
        inventory = Inventory.query.filter(
            and_(
                Inventory.product_sku == product_sku,
                Inventory.distribution_center_id == distribution_center_id
            )
        ).first()
        
        if not inventory:
            raise NotFoundError(
                f"No se encontró inventario para {product_sku} "
                f"en centro de distribución {distribution_center_id}"
            )
        
        # Validar que hay suficiente quantity_reserved
        if inventory.quantity_reserved < quantity:
            logger.warning(
                f"⚠️ Intentando liberar {quantity} unidades de {product_sku}, "
                f"pero solo hay {inventory.quantity_reserved} reservadas. "
                f"Liberando solo {inventory.quantity_reserved}."
            )
            quantity = inventory.quantity_reserved
        
        # Reducir quantity_reserved
        old_quantity_reserved = inventory.quantity_reserved
        inventory.quantity_reserved -= quantity
        inventory.last_movement_date = datetime.utcnow()
        
        released_item = {
            'product_sku': product_sku,
            'quantity_released': quantity,
            'distribution_center_id': distribution_center_id,
            'quantity_reserved_before': old_quantity_reserved,
            'quantity_reserved_after': inventory.quantity_reserved,
            'quantity_available': inventory.quantity_available
        }
        
        self.released_items.append(released_item)
        
        logger.info(
            f"🔓 Liberando inventario: {product_sku} - "
            f"Cantidad: {quantity} - "
            f"Reserved antes: {old_quantity_reserved} → después: {inventory.quantity_reserved}"
        )
    
    def _emit_websocket_event(self, released_item: Dict):
        """Emite evento WebSocket de liberación de inventario."""
        try:
            from src.websockets.websocket_manager import InventoryNotifier
            from src.commands.get_stock_levels import GetStockLevels
            
            # Obtener stock actualizado (con el cálculo correcto de disponible)
            stock_command = GetStockLevels(
                product_sku=released_item['product_sku'],
                include_reserved=True,
                include_in_transit=False
            )
            stock_data = stock_command.execute()
            
            # Emitir notificación WebSocket
            InventoryNotifier.notify_stock_change(
                product_sku=released_item['product_sku'],
                stock_data=stock_data,
                change_type=InventoryChangeType.RESERVATION_RELEASED
            )
            
            logger.info(
                f"📡 WebSocket: Notificado liberación de stock para {released_item['product_sku']} "
                f"(disponible: {stock_data.get('total_available')})"
            )
        except Exception as e:
            logger.warning(f"⚠️ Error emitiendo evento WebSocket: {str(e)}")
