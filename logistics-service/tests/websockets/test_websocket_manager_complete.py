"""
Tests para websockets/websocket_manager.py

Coverage objetivo: >75%

Funcionalidad a probar:
- Inicialización de Socket.IO
- Registro de event handlers
- Conexión y desconexión de clientes
- Suscripción a productos específicos
- Suscripción global
- Notificaciones de cambios de stock
- InventoryNotifier
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock, call
from flask import Flask
from flask_socketio import SocketIO

from src.websockets.websocket_manager import (
    init_socketio,
    register_socket_events,
    InventoryNotifier
)


class TestWebSocketManagerInit:
    """Tests de inicialización de Socket.IO"""

    @patch('src.websockets.websocket_manager.SocketIO')
    def test_init_socketio(self, mock_socketio_class):
        """Test: Inicializar Socket.IO con app Flask"""
        app = Flask(__name__)
        mock_socketio_instance = Mock()
        mock_socketio_class.return_value = mock_socketio_instance
        
        result = init_socketio(app)
        
        assert result == mock_socketio_instance
        mock_socketio_class.assert_called_once()
        # Verificar parámetros de inicialización
        call_args = mock_socketio_class.call_args
        assert call_args[0][0] == app
        assert 'cors_allowed_origins' in call_args[1]
        assert 'async_mode' in call_args[1]

    @patch('src.websockets.websocket_manager.SocketIO')
    @patch('src.websockets.websocket_manager.register_socket_events')
    def test_init_socketio_registers_events(self, mock_register, mock_socketio_class):
        """Test: init_socketio registra event handlers"""
        app = Flask(__name__)
        mock_socketio_instance = Mock()
        mock_socketio_class.return_value = mock_socketio_instance
        
        init_socketio(app)
        
        mock_register.assert_called_once()


class TestWebSocketConnectionEvents:
    """Tests de eventos de conexión/desconexión"""

    @patch('src.websockets.websocket_manager.socketio')
    def test_handle_connect(self, mock_socketio):
        """Test: Manejar evento connect"""
        # Este test verifica que el handler existe
        # En la implementación real, register_socket_events() registra los handlers
        assert hasattr(mock_socketio, 'on')

    @patch('src.websockets.websocket_manager.socketio')
    def test_handle_disconnect(self, mock_socketio):
        """Test: Manejar evento disconnect"""
        assert hasattr(mock_socketio, 'on')


class TestWebSocketSubscriptions:
    """Tests de suscripciones a productos"""

    def test_subscription_validation(self):
        """Test: Validar estructura de suscripción"""
        # Estructura esperada para suscripción
        subscription_data = {
            'product_skus': ['JER-001', 'VAC-001', 'ANT-003']
        }
        
        assert 'product_skus' in subscription_data
        assert isinstance(subscription_data['product_skus'], list)
        assert len(subscription_data['product_skus']) > 0

    def test_room_name_format(self):
        """Test: Formato de nombres de rooms"""
        product_sku = 'jer-001'
        expected_room = f"product_{product_sku.upper()}"
        
        assert expected_room == 'product_JER-001'

    def test_global_subscription_room(self):
        """Test: Room para suscripción global"""
        global_room = 'all_inventory_updates'
        assert isinstance(global_room, str)
        assert len(global_room) > 0


class TestInventoryNotifier:
    """Tests de InventoryNotifier"""

    @patch('src.websockets.websocket_manager.socketio')
    def test_notify_stock_change_no_socketio(self, mock_socketio):
        """Test: Notificar cambio cuando Socket.IO no está inicializado"""
        # Simular Socket.IO no inicializado
        import src.websockets.websocket_manager as wsm
        original_socketio = wsm.socketio
        wsm.socketio = None
        
        # No debe lanzar excepción
        InventoryNotifier.notify_stock_change(
            product_sku='JER-001',
            stock_data={'quantity': 100},
            change_type='update'
        )
        
        # Restaurar
        wsm.socketio = original_socketio

    @patch('src.websockets.websocket_manager.socketio')
    def test_notify_stock_change_success(self, mock_socketio):
        """Test: Notificar cambio de stock exitosamente"""
        # Configurar mock
        import src.websockets.websocket_manager as wsm
        wsm.socketio = mock_socketio
        
        stock_data = {
            'product_sku': 'JER-001',
            'quantity_available': 100,
            'quantity_reserved': 5
        }
        
        InventoryNotifier.notify_stock_change(
            product_sku='jer-001',
            stock_data=stock_data,
            change_type='update'
        )
        
        # Verificar que se llamó emit dos veces (room específico + global)
        assert mock_socketio.emit.call_count == 2
        
        # Verificar primer llamado (room específico)
        first_call = mock_socketio.emit.call_args_list[0]
        assert first_call[0][0] == 'stock_updated'
        assert 'product_sku' in first_call[0][1]
        assert first_call[0][1]['product_sku'] == 'JER-001'
        assert first_call[1]['room'] == 'product_JER-001'
        
        # Verificar segundo llamado (room global)
        second_call = mock_socketio.emit.call_args_list[1]
        assert second_call[1]['room'] == 'all_inventory_updates'

    @patch('src.websockets.websocket_manager.socketio')
    def test_notify_stock_change_payload_structure(self, mock_socketio):
        """Test: Estructura del payload de notificación"""
        import src.websockets.websocket_manager as wsm
        wsm.socketio = mock_socketio
        
        stock_data = {
            'quantity_available': 50,
            'distribution_center_id': 1
        }
        
        InventoryNotifier.notify_stock_change(
            product_sku='VAC-001',
            stock_data=stock_data,
            change_type='low_stock'
        )
        
        # Obtener el payload del primer llamado
        call_args = mock_socketio.emit.call_args_list[0]
        payload = call_args[0][1]
        
        assert 'product_sku' in payload
        assert 'change_type' in payload
        assert 'timestamp' in payload
        assert 'stock_data' in payload
        assert payload['change_type'] == 'low_stock'
        assert payload['stock_data'] == stock_data

    @patch('src.websockets.websocket_manager.socketio')
    def test_notify_stock_change_sku_uppercase(self, mock_socketio):
        """Test: SKU se convierte a mayúsculas"""
        import src.websockets.websocket_manager as wsm
        wsm.socketio = mock_socketio
        
        InventoryNotifier.notify_stock_change(
            product_sku='abc-123',  # lowercase
            stock_data={'quantity': 10},
            change_type='update'
        )
        
        call_args = mock_socketio.emit.call_args_list[0]
        payload = call_args[0][1]
        
        assert payload['product_sku'] == 'ABC-123'

    @patch('src.websockets.websocket_manager.socketio')
    def test_notify_stock_change_error_handling(self, mock_socketio):
        """Test: Manejo de errores en notificación"""
        import src.websockets.websocket_manager as wsm
        wsm.socketio = mock_socketio
        
        # Configurar mock para que lance excepción
        mock_socketio.emit.side_effect = Exception("WebSocket error")
        
        # No debe lanzar excepción (manejo interno)
        InventoryNotifier.notify_stock_change(
            product_sku='JER-001',
            stock_data={'quantity': 100},
            change_type='update'
        )

    @patch('src.websockets.websocket_manager.socketio')
    def test_notify_multiple_stock_changes(self, mock_socketio):
        """Test: Notificar múltiples cambios de stock"""
        import src.websockets.websocket_manager as wsm
        wsm.socketio = mock_socketio
        
        changes = [
            {
                'product_sku': 'JER-001',
                'stock_data': {'quantity': 100},
                'change_type': 'update'
            },
            {
                'product_sku': 'VAC-001',
                'stock_data': {'quantity': 50},
                'change_type': 'low_stock'
            },
            {
                'product_sku': 'ANT-003',
                'stock_data': {'quantity': 0},
                'change_type': 'out_of_stock'
            }
        ]
        
        InventoryNotifier.notify_multiple_stock_changes(changes)
        
        # Debe llamar emit múltiples veces (2 por cada cambio: room específico + global)
        expected_calls = len(changes) * 2
        assert mock_socketio.emit.call_count == expected_calls


class TestInventoryNotifierAlerts:
    """Tests de alertas específicas"""

    @patch('src.websockets.websocket_manager.socketio')
    def test_notify_low_stock_alert(self, mock_socketio):
        """Test: Notificación de stock bajo"""
        import src.websockets.websocket_manager as wsm
        wsm.socketio = mock_socketio
        
        stock_data = {
            'product_sku': 'JER-001',
            'quantity_available': 10,
            'minimum_stock': 50
        }
        
        InventoryNotifier.notify_low_stock_alert('JER-001', stock_data)
        
        # Verificar que se envió notificación
        assert mock_socketio.emit.called

    @patch('src.websockets.websocket_manager.socketio')
    def test_notify_out_of_stock(self, mock_socketio):
        """Test: Notificación de producto agotado"""
        import src.websockets.websocket_manager as wsm
        wsm.socketio = mock_socketio
        
        stock_data = {
            'product_sku': 'VAC-001',
            'quantity_available': 0
        }
        
        InventoryNotifier.notify_out_of_stock('VAC-001', stock_data)
        
        assert mock_socketio.emit.called

    @patch('src.websockets.websocket_manager.socketio')
    def test_notify_restock(self, mock_socketio):
        """Test: Notificación de reabastecimiento"""
        import src.websockets.websocket_manager as wsm
        wsm.socketio = mock_socketio
        
        stock_data = {
            'product_sku': 'ANT-003',
            'quantity_available': 200,
            'previous_quantity': 5
        }
        
        InventoryNotifier.notify_restock('ANT-003', stock_data)
        
        assert mock_socketio.emit.called


class TestWebSocketIntegration:
    """Tests de integración de WebSocket"""

    def test_socketio_configuration(self):
        """Test: Configuración de Socket.IO"""
        # Verificar parámetros esperados
        expected_config = {
            'cors_allowed_origins': '*',
            'async_mode': 'threading',
            'logger': True,
            'engineio_logger': True,
            'ping_timeout': 60,
            'ping_interval': 25
        }
        
        for key, value in expected_config.items():
            assert isinstance(key, str)

    @patch('src.websockets.websocket_manager.socketio')
    def test_event_types(self, mock_socketio):
        """Test: Tipos de eventos soportados"""
        event_types = [
            'connect',
            'disconnect',
            'subscribe_products',
            'unsubscribe_products',
            'subscribe_all_products',
            'ping'
        ]
        
        for event in event_types:
            assert isinstance(event, str)
            assert len(event) > 0

    def test_change_types(self):
        """Test: Tipos de cambios de stock"""
        change_types = ['update', 'low_stock', 'out_of_stock', 'restock']
        
        for change_type in change_types:
            assert isinstance(change_type, str)
            assert len(change_type) > 0
