"""
WebSocket Manager for Real-Time Inventory Updates.

Este módulo maneja las conexiones WebSocket y envía notificaciones
en tiempo real cuando el inventario cambia.
"""

from flask_socketio import SocketIO, emit, join_room, leave_room
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

# Instancia global de SocketIO (será inicializada desde main.py)
socketio: Optional[SocketIO] = None


def init_socketio(app):
    """
    Inicializa Socket.IO con la aplicación Flask.
    
    Args:
        app: Instancia de Flask
    
    Returns:
        SocketIO instance
    """
    global socketio
    
    socketio = SocketIO(
        app,
        cors_allowed_origins="*",  # En producción, especificar dominios permitidos
        async_mode='threading',
        logger=True,
        engineio_logger=True,
        ping_timeout=60,
        ping_interval=25
    )
    
    # Registrar event handlers
    register_socket_events()
    
    logger.info("✅ Socket.IO initialized successfully")
    return socketio


def register_socket_events():
    """Registra los manejadores de eventos de Socket.IO."""
    
    @socketio.on('connect')
    def handle_connect():
        """Maneja nueva conexión de cliente."""
        logger.info(f"🔌 Cliente conectado: {request.sid}")
        emit('connection_established', {
            'status': 'connected',
            'message': 'Conectado al servidor de inventario en tiempo real'
        })
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Maneja desconexión de cliente."""
        logger.info(f"🔌 Cliente desconectado: {request.sid}")
    
    @socketio.on('subscribe_products')
    def handle_subscribe_products(data):
        """
        Suscribir cliente a actualizaciones de productos específicos.
        
        Payload esperado:
        {
            "product_skus": ["JER-001", "VAC-001"]
        }
        """
        try:
            product_skus = data.get('product_skus', [])
            
            if not product_skus:
                emit('error', {'message': 'product_skus requerido'})
                return
            
            # Unir cliente a rooms por cada SKU
            for sku in product_skus:
                room_name = f"product_{sku.upper()}"
                join_room(room_name)
                logger.info(f"📦 Cliente {request.sid} suscrito a {room_name}")
            
            emit('subscribed', {
                'product_skus': product_skus,
                'message': f'Suscrito a {len(product_skus)} productos'
            })
            
        except Exception as e:
            logger.error(f"❌ Error en suscripción: {str(e)}")
            emit('error', {'message': str(e)})
    
    @socketio.on('unsubscribe_products')
    def handle_unsubscribe_products(data):
        """
        Desuscribir cliente de actualizaciones de productos.
        
        Payload esperado:
        {
            "product_skus": ["JER-001", "VAC-001"]
        }
        """
        try:
            product_skus = data.get('product_skus', [])
            
            for sku in product_skus:
                room_name = f"product_{sku.upper()}"
                leave_room(room_name)
                logger.info(f"📦 Cliente {request.sid} desuscrito de {room_name}")
            
            emit('unsubscribed', {
                'product_skus': product_skus
            })
            
        except Exception as e:
            logger.error(f"❌ Error en desuscripción: {str(e)}")
            emit('error', {'message': str(e)})
    
    @socketio.on('subscribe_all_products')
    def handle_subscribe_all():
        """Suscribir cliente a TODOS los cambios de inventario."""
        try:
            join_room('all_inventory_updates')
            logger.info(f"📦 Cliente {request.sid} suscrito a TODOS los productos")
            
            emit('subscribed_all', {
                'message': 'Suscrito a todas las actualizaciones de inventario'
            })
            
        except Exception as e:
            logger.error(f"❌ Error en suscripción global: {str(e)}")
            emit('error', {'message': str(e)})
    
    @socketio.on('ping')
    def handle_ping():
        """Responde a ping del cliente (mantener conexión viva)."""
        emit('pong', {'timestamp': datetime.utcnow().isoformat()})


class InventoryNotifier:
    """
    Clase para enviar notificaciones de cambios de inventario
    a través de WebSockets.
    """
    
    @staticmethod
    def notify_stock_change(
        product_sku: str,
        stock_data: Dict,
        change_type: str = 'update'
    ):
        """
        Notifica cambio de stock a clientes suscritos.
        
        Args:
            product_sku: SKU del producto
            stock_data: Información del stock actualizado
            change_type: Tipo de cambio ('update', 'low_stock', 'out_of_stock', 'restock')
        """
        if not socketio:
            logger.warning("⚠️ Socket.IO no inicializado")
            return
        
        try:
            product_sku_upper = product_sku.upper()
            room_name = f"product_{product_sku_upper}"
            
            payload = {
                'product_sku': product_sku_upper,
                'change_type': change_type,
                'timestamp': datetime.utcnow().isoformat(),
                'stock_data': stock_data
            }
            
            # Notificar a suscriptores específicos del producto
            socketio.emit(
                'stock_updated',
                payload,
                room=room_name
            )
            
            # Notificar a suscriptores de TODOS los productos
            socketio.emit(
                'stock_updated',
                payload,
                room='all_inventory_updates'
            )
            
            logger.info(f"📤 Notificación enviada: {product_sku_upper} - {change_type}")
            
        except Exception as e:
            logger.error(f"❌ Error enviando notificación: {str(e)}")
    
    @staticmethod
    def notify_multiple_stock_changes(changes: List[Dict]):
        """
        Notifica múltiples cambios de stock en una sola operación.
        
        Args:
            changes: Lista de cambios, cada uno con:
                     {
                         'product_sku': 'JER-001',
                         'stock_data': {...},
                         'change_type': 'update'
                     }
        """
        if not socketio:
            logger.warning("⚠️ Socket.IO no inicializado")
            return
        
        try:
            for change in changes:
                InventoryNotifier.notify_stock_change(
                    product_sku=change['product_sku'],
                    stock_data=change['stock_data'],
                    change_type=change.get('change_type', 'update')
                )
            
            logger.info(f"📤 {len(changes)} notificaciones batch enviadas")
            
        except Exception as e:
            logger.error(f"❌ Error enviando notificaciones batch: {str(e)}")
    
    @staticmethod
    def notify_low_stock_alert(product_sku: str, stock_data: Dict):
        """
        Notifica alerta de stock bajo.
        
        Args:
            product_sku: SKU del producto
            stock_data: Información del stock
        """
        InventoryNotifier.notify_stock_change(
            product_sku=product_sku,
            stock_data=stock_data,
            change_type='low_stock'
        )
    
    @staticmethod
    def notify_out_of_stock(product_sku: str, stock_data: Dict):
        """
        Notifica que un producto se agotó.
        
        Args:
            product_sku: SKU del producto
            stock_data: Información del stock
        """
        InventoryNotifier.notify_stock_change(
            product_sku=product_sku,
            stock_data=stock_data,
            change_type='out_of_stock'
        )
    
    @staticmethod
    def notify_restock(product_sku: str, stock_data: Dict):
        """
        Notifica que un producto fue reabastecido.
        
        Args:
            product_sku: SKU del producto
            stock_data: Información del stock
        """
        InventoryNotifier.notify_stock_change(
            product_sku=product_sku,
            stock_data=stock_data,
            change_type='restock'
        )


# Importaciones necesarias para los decoradores
from flask import request
from datetime import datetime
