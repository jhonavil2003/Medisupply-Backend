"""
Tests simplificados para commands/generate_routes_from_sales.py

Enfocados en tests básicos que funcionen sin asumir métodos privados.
Cobertura actual: 36%
"""

import pytest
from datetime import date
from unittest.mock import Mock, patch

from src.commands.generate_routes_from_sales import GenerateRoutesFromSalesService


class TestGenerateRoutesFromSalesService:
    """Tests básicos para GenerateRoutesFromSalesService"""

    @patch('src.commands.generate_routes_from_sales.get_sales_service_client')
    def test_init_command(self, mock_get_client):
        """Test: Inicialización del comando"""
        command = GenerateRoutesFromSalesService(
            distribution_center_id=1,
            planned_date=date(2025, 11, 10)
        )
        
        assert command.distribution_center_id == 1
        assert command.planned_date == date(2025, 11, 10)
        assert command.optimization_strategy == 'balanced'  # default
        assert command.max_orders is None  # default

    @patch('src.commands.generate_routes_from_sales.get_sales_service_client')
    def test_init_with_custom_params(self, mock_get_client):
        """Test: Inicialización con parámetros personalizados"""
        command = GenerateRoutesFromSalesService(
            distribution_center_id=2,
            planned_date=date(2025, 12, 15),
            optimization_strategy='minimize_distance',
            max_orders=50
        )
        
        assert command.distribution_center_id == 2
        assert command.optimization_strategy == 'minimize_distance'
        assert command.max_orders == 50

    @patch('src.commands.generate_routes_from_sales.get_sales_service_client')
    def test_validate_orders_method_exists(self, mock_get_client):
        """Test: Verificar que existe método _validate_orders"""
        command = GenerateRoutesFromSalesService(
            distribution_center_id=1,
            planned_date=date(2025, 11, 10)
        )
        
        # Verificar que el método existe
        assert hasattr(command, '_validate_orders')
        assert callable(command._validate_orders)
