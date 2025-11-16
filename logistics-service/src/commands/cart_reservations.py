"""
Comandos para gestionar reservas de carrito de compra.

Estos comandos permiten:
- Reservar stock temporalmente cuando se agrega al carrito
- Liberar stock cuando se remueve del carrito
- Actualizar cantidades reservadas
- Expirar reservas automáticamente
"""

from datetime import datetime
from typing import Optional, List, Dict
from sqlalchemy import and_
from src.session import db
from src.models.cart_reservation import CartReservation
from src.models.inventory import Inventory
from src.errors.errors import ValidationError, NotFoundError, ConflictError
from src.websockets.inventory_events import InventoryChangeType
import logging

logger = logging.getLogger(__name__)


class ReserveStockCommand:
    """
    Comando para reservar stock temporalmente en el carrito.
    
    Flujo:
    1. Validar que existe stock disponible
    2. Crear o actualizar reserva temporal
    3. Calcular stock disponible actualizado
    4. Emitir evento WebSocket
    """
    
    def __init__(
        self,
        product_sku: str,
        quantity: int,
        user_id: str,
        session_id: str,
        distribution_center_id: Optional[int] = None,
        ttl_minutes: int = 15
    ):
        self.product_sku = product_sku.upper()
        self.quantity = quantity
        self.user_id = user_id
        self.session_id = session_id
        self.distribution_center_id = distribution_center_id
        self.ttl_minutes = ttl_minutes
    
    def execute(self) -> Dict:
        """Ejecuta la reserva de stock."""
        # Validar parámetros
        self._validate_parameters()
        
        # Obtener stock disponible real (sin reservas de carrito)
        available_stock = self._get_available_stock()
        
        if available_stock < self.quantity:
            raise ConflictError(
                f"Stock insuficiente para {self.product_sku}. "
                f"Solicitado: {self.quantity}, Disponible: {available_stock}"
            )
        
        # Buscar reserva existente
        existing_reservation = CartReservation.query.filter(
            and_(
                CartReservation.product_sku == self.product_sku,
                CartReservation.distribution_center_id == self.distribution_center_id,
                CartReservation.user_id == self.user_id,
                CartReservation.session_id == self.session_id,
                CartReservation.is_active == True
            )
        ).first()
        
        if existing_reservation:
            # Actualizar reserva existente
            new_quantity = existing_reservation.quantity_reserved + self.quantity
            
            # Validar que hay suficiente stock para la nueva cantidad
            if available_stock < self.quantity:  # Solo la cantidad adicional
                raise ConflictError(
                    f"Stock insuficiente para aumentar reserva. "
                    f"Disponible: {available_stock}"
                )
            
            existing_reservation.quantity_reserved = new_quantity
            existing_reservation.expires_at = CartReservation.get_default_expiration(self.ttl_minutes)
            existing_reservation.updated_at = datetime.utcnow()
            
            reservation = existing_reservation
        else:
            # Crear nueva reserva
            reservation = CartReservation(
                product_sku=self.product_sku,
                distribution_center_id=self.distribution_center_id,
                user_id=self.user_id,
                session_id=self.session_id,
                quantity_reserved=self.quantity,
                expires_at=CartReservation.get_default_expiration(self.ttl_minutes),
                is_active=True
            )
            db.session.add(reservation)
        
        try:
            db.session.commit()
            
            # Obtener stock actualizado para el evento WebSocket
            updated_stock = self._get_stock_for_websocket()
            
            # Emitir evento WebSocket
            self._emit_websocket_event(updated_stock, InventoryChangeType.RESERVATION)
            
            logger.info(
                f"✅ Stock reservado: {self.product_sku} - "
                f"Cantidad: {self.quantity} - Usuario: {self.user_id}"
            )
            
            return {
                'success': True,
                'reservation_id': reservation.id,
                'product_sku': self.product_sku,
                'quantity_reserved': reservation.quantity_reserved,
                'stock_available': updated_stock.get('total_available', 0),
                'expires_at': reservation.expires_at.isoformat(),
                'remaining_time_seconds': reservation.remaining_time_seconds,
                'message': 'Stock reservado exitosamente'
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Error reservando stock: {str(e)}")
            raise
    
    def _validate_parameters(self):
        """Valida los parámetros de entrada."""
        if not self.product_sku:
            raise ValidationError("product_sku es requerido")
        
        if not self.user_id:
            raise ValidationError("user_id es requerido")
        
        if not self.session_id:
            raise ValidationError("session_id es requerido")
        
        if self.quantity <= 0:
            raise ValidationError("quantity debe ser mayor a 0")
        
        if self.ttl_minutes <= 0:
            raise ValidationError("ttl_minutes debe ser mayor a 0")
    
    def _get_available_stock(self) -> int:
        """
        Obtiene el stock disponible real.
        
        Stock disponible = Stock total - Reservas confirmadas - Reservas de carrito activas
        """
        # Obtener inventario total
        query = Inventory.query.filter(Inventory.product_sku == self.product_sku)
        
        if self.distribution_center_id:
            query = query.filter(Inventory.distribution_center_id == self.distribution_center_id)
        
        inventories = query.all()
        
        if not inventories:
            raise NotFoundError(f"Producto {self.product_sku} no encontrado en inventario")
        
        # Sumar stock disponible de todos los centros
        total_available = sum(inv.quantity_available for inv in inventories)
        
        # Restar reservas de carrito activas (excluyendo la del usuario actual)
        active_reservations = CartReservation.query.filter(
            and_(
                CartReservation.product_sku == self.product_sku,
                CartReservation.is_active == True,
                CartReservation.expires_at > datetime.utcnow(),
                # Excluir reserva del usuario actual
                ~and_(
                    CartReservation.user_id == self.user_id,
                    CartReservation.session_id == self.session_id
                )
            )
        ).all()
        
        total_cart_reserved = sum(r.quantity_reserved for r in active_reservations)
        
        return max(0, total_available - total_cart_reserved)
    
    def _get_stock_for_websocket(self) -> Dict:
        """Obtiene información de stock para evento WebSocket."""
        from src.commands.get_stock_levels import GetStockLevels
        
        command = GetStockLevels(product_sku=self.product_sku)
        stock_result = command.execute()
        
        # Calcular total de reservas de carrito
        total_cart_reserved = CartReservation.query.filter(
            and_(
                CartReservation.product_sku == self.product_sku,
                CartReservation.is_active == True,
                CartReservation.expires_at > datetime.utcnow()
            )
        ).with_entities(
            db.func.sum(CartReservation.quantity_reserved)
        ).scalar() or 0
        
        # Ajustar el stock disponible restando las reservas de carrito
        stock_result['total_cart_reserved'] = int(total_cart_reserved)
        stock_result['total_available'] = max(
            0,
            stock_result.get('total_available', 0) - int(total_cart_reserved)
        )
        
        return stock_result
    
    def _emit_websocket_event(self, stock_data: Dict, change_type: str):
        """Emite evento WebSocket de cambio de stock."""
        from src.websockets.websocket_manager import InventoryNotifier
        
        try:
            InventoryNotifier.notify_stock_change(
                product_sku=self.product_sku,
                stock_data=stock_data,
                change_type=change_type
            )
        except Exception as e:
            logger.warning(f"⚠️ No se pudo emitir evento WebSocket: {str(e)}")


class ReleaseStockCommand:
    """
    Comando para liberar stock reservado en el carrito.
    
    Se usa cuando:
    - El usuario remueve un producto del carrito
    - El usuario decrementa la cantidad
    - El usuario cierra la app
    """
    
    def __init__(
        self,
        product_sku: str,
        quantity: int,
        user_id: str,
        session_id: str
    ):
        self.product_sku = product_sku.upper()
        self.quantity = quantity
        self.user_id = user_id
        self.session_id = session_id
    
    def execute(self) -> Dict:
        """Ejecuta la liberación de stock."""
        # Buscar reserva activa
        reservation = CartReservation.query.filter(
            and_(
                CartReservation.product_sku == self.product_sku,
                CartReservation.user_id == self.user_id,
                CartReservation.session_id == self.session_id,
                CartReservation.is_active == True
            )
        ).first()
        
        if not reservation:
            # No hay reserva activa, no hacer nada
            logger.warning(
                f"⚠️ No se encontró reserva activa para liberar: "
                f"{self.product_sku} - Usuario: {self.user_id}"
            )
            return {
                'success': True,
                'message': 'No hay reserva activa para liberar',
                'stock_available': 0
            }
        
        # Reducir cantidad o desactivar reserva
        released_quantity = self.quantity
        remaining_quantity = 0
        
        if self.quantity >= reservation.quantity_reserved:
            # Liberar toda la reserva - eliminarla de la base de datos
            released_quantity = reservation.quantity_reserved
            remaining_quantity = 0
            db.session.delete(reservation)
        else:
            # Reducir cantidad
            reservation.quantity_reserved -= self.quantity
            reservation.updated_at = datetime.utcnow()
            remaining_quantity = reservation.quantity_reserved
        
        try:
            db.session.commit()
            
            # Obtener stock actualizado
            updated_stock = self._get_stock_for_websocket()
            
            # Emitir evento WebSocket
            self._emit_websocket_event(updated_stock, InventoryChangeType.RESERVATION_RELEASED)
            
            logger.info(
                f"✅ Stock liberado: {self.product_sku} - "
                f"Cantidad: {released_quantity} - Usuario: {self.user_id}"
            )
            
            return {
                'success': True,
                'product_sku': self.product_sku,
                'quantity_released': released_quantity,
                'remaining_reserved': remaining_quantity,
                'stock_available': updated_stock.get('total_available', 0),
                'message': 'Stock liberado exitosamente'
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Error liberando stock: {str(e)}")
            raise
    
    def _get_stock_for_websocket(self) -> Dict:
        """Obtiene información de stock para evento WebSocket."""
        from src.commands.get_stock_levels import GetStockLevels
        
        command = GetStockLevels(product_sku=self.product_sku)
        stock_result = command.execute()
        
        # Calcular total de reservas de carrito
        total_cart_reserved = CartReservation.query.filter(
            and_(
                CartReservation.product_sku == self.product_sku,
                CartReservation.is_active == True,
                CartReservation.expires_at > datetime.utcnow()
            )
        ).with_entities(
            db.func.sum(CartReservation.quantity_reserved)
        ).scalar() or 0
        
        stock_result['total_cart_reserved'] = int(total_cart_reserved)
        stock_result['total_available'] = max(
            0,
            stock_result.get('total_available', 0) - int(total_cart_reserved)
        )
        
        return stock_result
    
    def _emit_websocket_event(self, stock_data: Dict, change_type: str):
        """Emite evento WebSocket de cambio de stock."""
        from src.websockets.websocket_manager import InventoryNotifier
        
        try:
            InventoryNotifier.notify_stock_change(
                product_sku=self.product_sku,
                stock_data=stock_data,
                change_type=change_type
            )
        except Exception as e:
            logger.warning(f"⚠️ No se pudo emitir evento WebSocket: {str(e)}")


class ExpireCartReservationsCommand:
    """
    Comando para expirar reservas de carrito antiguas.
    
    Este comando debe ejecutarse periódicamente (cada minuto)
    como un background job.
    """
    
    def execute(self) -> Dict:
        """Expira reservas de carrito que hayan superado su TTL."""
        # Buscar reservas expiradas
        expired_reservations = CartReservation.query.filter(
            and_(
                CartReservation.is_active == True,
                CartReservation.expires_at <= datetime.utcnow()
            )
        ).all()
        
        if not expired_reservations:
            logger.debug("🔄 No hay reservas expiradas para procesar")
            return {
                'success': True,
                'expired_count': 0,
                'message': 'No hay reservas expiradas'
            }
        
        # Agrupar por producto SKU para emitir eventos WebSocket
        products_affected = {}
        for reservation in expired_reservations:
            sku = reservation.product_sku
            if sku not in products_affected:
                products_affected[sku] = 0
            products_affected[sku] += reservation.quantity_reserved
            
            # Desactivar reserva
            reservation.is_active = False
            reservation.updated_at = datetime.utcnow()
        
        try:
            db.session.commit()
            
            # Emitir eventos WebSocket para cada producto afectado
            for product_sku, quantity in products_affected.items():
                self._emit_websocket_event_for_product(product_sku)
            
            logger.info(
                f"✅ Expiradas {len(expired_reservations)} reservas de carrito - "
                f"Productos afectados: {len(products_affected)}"
            )
            
            return {
                'success': True,
                'expired_count': len(expired_reservations),
                'products_affected': list(products_affected.keys()),
                'message': f'{len(expired_reservations)} reservas expiradas'
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Error expirando reservas: {str(e)}")
            raise
    
    def _emit_websocket_event_for_product(self, product_sku: str):
        """Emite evento WebSocket para un producto cuyo stock cambió."""
        from src.commands.get_stock_levels import GetStockLevels
        from src.websockets.websocket_manager import InventoryNotifier
        
        try:
            # Obtener stock actualizado
            command = GetStockLevels(product_sku=product_sku)
            stock_result = command.execute()
            
            # Calcular reservas de carrito
            total_cart_reserved = CartReservation.query.filter(
                and_(
                    CartReservation.product_sku == product_sku,
                    CartReservation.is_active == True,
                    CartReservation.expires_at > datetime.utcnow()
                )
            ).with_entities(
                db.func.sum(CartReservation.quantity_reserved)
            ).scalar() or 0
            
            stock_result['total_cart_reserved'] = int(total_cart_reserved)
            stock_result['total_available'] = max(
                0,
                stock_result.get('total_available', 0) - int(total_cart_reserved)
            )
            
            # Emitir evento
            InventoryNotifier.notify_stock_change(
                product_sku=product_sku,
                stock_data=stock_result,
                change_type='cart_reservation_expired'
            )
            
        except Exception as e:
            logger.warning(
                f"⚠️ No se pudo emitir evento WebSocket para {product_sku}: {str(e)}"
            )


class ClearUserCartReservationsCommand:
    """
    Comando para limpiar todas las reservas de un usuario.
    
    Se usa cuando:
    - El usuario confirma la orden (las reservas pasan a quantity_reserved)
    - El usuario cierra sesión
    - El usuario cancela su carrito
    """
    
    def __init__(self, user_id: str, session_id: str):
        self.user_id = user_id
        self.session_id = session_id
    
    def execute(self) -> Dict:
        """Limpia todas las reservas del usuario (activas o inactivas)."""
        # Buscar TODAS las reservas del usuario (activas o no)
        reservations = CartReservation.query.filter(
            and_(
                CartReservation.user_id == self.user_id,
                CartReservation.session_id == self.session_id
            )
        ).all()
        
        if not reservations:
            return {
                'success': True,
                'cleared_count': 0,
                'message': 'No hay reservas para limpiar'
            }
        
        # Agrupar productos afectados y eliminar reservas
        products_affected = set()
        for reservation in reservations:
            products_affected.add(reservation.product_sku)
            db.session.delete(reservation)
        
        try:
            db.session.commit()
            
            # Emitir eventos WebSocket
            for product_sku in products_affected:
                self._emit_websocket_event_for_product(product_sku)
            
            logger.info(
                f"✅ Limpiadas {len(reservations)} reservas del usuario {self.user_id}"
            )
            
            return {
                'success': True,
                'cleared_count': len(reservations),
                'products_affected': list(products_affected),
                'message': f'{len(reservations)} reservas liberadas'
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Error limpiando reservas: {str(e)}")
            raise
    
    def _emit_websocket_event_for_product(self, product_sku: str):
        """Emite evento WebSocket para un producto."""
        from src.commands.get_stock_levels import GetStockLevels
        from src.websockets.websocket_manager import InventoryNotifier
        
        try:
            command = GetStockLevels(product_sku=product_sku)
            stock_result = command.execute()
            
            total_cart_reserved = CartReservation.query.filter(
                and_(
                    CartReservation.product_sku == product_sku,
                    CartReservation.is_active == True,
                    CartReservation.expires_at > datetime.utcnow()
                )
            ).with_entities(
                db.func.sum(CartReservation.quantity_reserved)
            ).scalar() or 0
            
            stock_result['total_cart_reserved'] = int(total_cart_reserved)
            stock_result['total_available'] = max(
                0,
                stock_result.get('total_available', 0) - int(total_cart_reserved)
            )
            
            InventoryNotifier.notify_stock_change(
                product_sku=product_sku,
                stock_data=stock_result,
                change_type=InventoryChangeType.RESERVATION_RELEASED
            )
            
        except Exception as e:
            logger.warning(f"⚠️ Error emitiendo evento WebSocket: {str(e)}")
