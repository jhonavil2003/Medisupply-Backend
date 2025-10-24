"""
Tests adicionales para el blueprint DELETE /orders/{id}.
Cubre casos de errores y excepciones no controladas.
"""
import pytest
import json
from unittest.mock import patch
from src.commands.delete_order import DeleteOrder


class TestDeleteOrderBlueprint:
    """Tests para el endpoint DELETE /orders/{id}."""
    
    def test_delete_order_unexpected_exception(self, client, sample_order, monkeypatch):
        """Test que una excepción inesperada retorna 500."""
        # Simular una excepción inesperada en DeleteOrder
        def mock_execute(self):
            raise RuntimeError("Unexpected error in delete")
        
        monkeypatch.setattr(DeleteOrder, 'execute', mock_execute)
        
        response = client.delete(f'/orders/{sample_order.id}')
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Internal server error' in data['error']
        assert data['status_code'] == 500
    
    def test_delete_order_database_connection_error(self, client, sample_order, monkeypatch):
        """Test error de conexión a base de datos."""
        from sqlalchemy.exc import OperationalError
        
        def mock_execute(self):
            raise OperationalError("statement", "params", "Connection lost")
        
        monkeypatch.setattr(DeleteOrder, 'execute', mock_execute)
        
        response = client.delete(f'/orders/{sample_order.id}')
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data
        assert data['status_code'] == 500
