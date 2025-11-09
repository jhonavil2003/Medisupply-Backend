"""
Tests adicionales para GetOrders - Filtros de fechas.
Cubre los filtros de delivery_date y order_date que faltan.
"""
import pytest
from datetime import datetime, timedelta
from src.commands.get_orders import GetOrders
from src.models.order import Order


class TestGetOrdersDateFilters:
    """Tests para filtros de fecha en GetOrders."""
    
    def test_get_orders_filter_by_delivery_date_from(self, db, sample_order):
        """Test filtro por delivery_date_from."""
        # Establecer fecha de entrega
        delivery_date = datetime.utcnow() + timedelta(days=7)
        sample_order.delivery_date = delivery_date
        db.session.commit()
        
        # Filtrar desde hace 1 día (debe incluir la orden)
        date_from = (datetime.utcnow() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        command = GetOrders(delivery_date_from=date_from)
        result = command.execute()
        
        assert len(result['orders']) >= 1
        assert any(o['id'] == sample_order.id for o in result['orders'])
    
    def test_get_orders_filter_by_delivery_date_from_excludes_earlier(self, db, sample_order):
        """Test que delivery_date_from excluye órdenes anteriores."""
        # Establecer fecha de entrega en el pasado
        past_date = datetime.utcnow() - timedelta(days=10)
        sample_order.delivery_date = past_date
        db.session.commit()
        
        # Filtrar desde hace 5 días (debe excluir la orden)
        date_from = (datetime.utcnow() - timedelta(days=5)).strftime('%Y-%m-%d')
        
        command = GetOrders(delivery_date_from=date_from)
        result = command.execute()
        
        # La orden con fecha pasada no debe estar
        assert not any(o['id'] == sample_order.id for o in result['orders'])
    
    def test_get_orders_filter_by_delivery_date_to(self, db, sample_order):
        """Test filtro por delivery_date_to."""
        # Establecer fecha de entrega
        delivery_date = datetime.utcnow() + timedelta(days=3)
        sample_order.delivery_date = delivery_date
        db.session.commit()
        
        # Filtrar hasta dentro de 10 días (debe incluir la orden)
        date_to = (datetime.utcnow() + timedelta(days=10)).strftime('%Y-%m-%d')
        
        command = GetOrders(delivery_date_to=date_to)
        result = command.execute()
        
        assert len(result['orders']) >= 1
        assert any(o['id'] == sample_order.id for o in result['orders'])
    
    def test_get_orders_filter_by_delivery_date_to_excludes_later(self, db, sample_order):
        """Test que delivery_date_to excluye órdenes posteriores."""
        # Establecer fecha de entrega en el futuro lejano
        future_date = datetime.utcnow() + timedelta(days=30)
        sample_order.delivery_date = future_date
        db.session.commit()
        
        # Filtrar hasta dentro de 5 días (debe excluir la orden)
        date_to = (datetime.utcnow() + timedelta(days=5)).strftime('%Y-%m-%d')
        
        command = GetOrders(delivery_date_to=date_to)
        result = command.execute()
        
        # La orden con fecha futura no debe estar
        assert not any(o['id'] == sample_order.id for o in result['orders'])
    
    def test_get_orders_filter_by_delivery_date_range(self, db, sample_order):
        """Test filtro por rango de delivery_date (from + to)."""
        # Establecer fecha de entrega
        delivery_date = datetime.utcnow() + timedelta(days=7)
        sample_order.delivery_date = delivery_date
        db.session.commit()
        
        # Rango de 1 a 10 días
        date_from = (datetime.utcnow() + timedelta(days=1)).strftime('%Y-%m-%d')
        date_to = (datetime.utcnow() + timedelta(days=10)).strftime('%Y-%m-%d')
        
        command = GetOrders(delivery_date_from=date_from, delivery_date_to=date_to)
        result = command.execute()
        
        assert len(result['orders']) >= 1
        assert any(o['id'] == sample_order.id for o in result['orders'])
    
    def test_get_orders_filter_by_order_date_from(self, db, sample_order):
        """Test filtro por order_date_from."""
        # La orden se creó hoy
        date_from = (datetime.utcnow() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        command = GetOrders(order_date_from=date_from)
        result = command.execute()
        
        assert len(result['orders']) >= 1
        assert any(o['id'] == sample_order.id for o in result['orders'])
    
    def test_get_orders_filter_by_order_date_from_excludes_earlier(self, db, sample_order):
        """Test que order_date_from excluye órdenes anteriores."""
        # Filtrar desde mañana (debe excluir órdenes de hoy)
        date_from = (datetime.utcnow() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        command = GetOrders(order_date_from=date_from)
        result = command.execute()
        
        # La orden de hoy no debe estar
        assert not any(o['id'] == sample_order.id for o in result['orders'])
    
    def test_get_orders_filter_by_order_date_to(self, db, sample_order):
        """Test filtro por order_date_to."""
        # La orden se creó hoy
        date_to = (datetime.utcnow() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        command = GetOrders(order_date_to=date_to)
        result = command.execute()
        
        assert len(result['orders']) >= 1
        assert any(o['id'] == sample_order.id for o in result['orders'])
    
    def test_get_orders_filter_by_order_date_to_excludes_later(self, db, sample_order):
        """Test que order_date_to excluye órdenes posteriores."""
        # Filtrar hasta ayer (debe excluir órdenes de hoy)
        date_to = (datetime.utcnow() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        command = GetOrders(order_date_to=date_to)
        result = command.execute()
        
        # La orden de hoy no debe estar
        assert not any(o['id'] == sample_order.id for o in result['orders'])
    
    def test_get_orders_filter_by_order_date_range(self, db, sample_order):
        """Test filtro por rango de order_date (from + to)."""
        date_from = (datetime.utcnow() - timedelta(days=1)).strftime('%Y-%m-%d')
        date_to = (datetime.utcnow() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        command = GetOrders(order_date_from=date_from, order_date_to=date_to)
        result = command.execute()
        
        assert len(result['orders']) >= 1
        assert any(o['id'] == sample_order.id for o in result['orders'])
    
    def test_get_orders_invalid_delivery_date_from_format(self, db, sample_order):
        """Test con formato de fecha inválido en delivery_date_from."""
        # Formato inválido - debe ser ignorado silenciosamente
        command = GetOrders(delivery_date_from='invalid-date')
        result = command.execute()
        
        # Debe retornar todas las órdenes sin filtrar
        assert len(result['orders']) >= 1
    
    def test_get_orders_invalid_delivery_date_to_format(self, db, sample_order):
        """Test con formato de fecha inválido en delivery_date_to."""
        # Formato inválido - debe ser ignorado silenciosamente
        command = GetOrders(delivery_date_to='not-a-date')
        result = command.execute()
        
        # Debe retornar todas las órdenes sin filtrar
        assert len(result['orders']) >= 1
    
    def test_get_orders_invalid_order_date_from_format(self, db, sample_order):
        """Test con formato de fecha inválido en order_date_from."""
        # Formato inválido - debe ser ignorado silenciosamente
        command = GetOrders(order_date_from='2025-13-45')  # Mes y día inválidos
        result = command.execute()
        
        # Debe retornar todas las órdenes sin filtrar
        assert len(result['orders']) >= 1
    
    def test_get_orders_invalid_order_date_to_format(self, db, sample_order):
        """Test con formato de fecha inválido en order_date_to."""
        # Formato inválido - debe ser ignorado silenciosamente
        command = GetOrders(order_date_to='25/10/2025')  # Formato incorrecto
        result = command.execute()
        
        # Debe retornar todas las órdenes sin filtrar
        assert len(result['orders']) >= 1
    
    def test_get_orders_combined_all_date_filters(self, db, sample_order):
        """Test combinando todos los filtros de fecha."""
        # Establecer fecha de entrega
        delivery_date = datetime.utcnow() + timedelta(days=7)
        sample_order.delivery_date = delivery_date
        db.session.commit()
        
        # Filtros de fechas
        delivery_from = (datetime.utcnow() + timedelta(days=1)).strftime('%Y-%m-%d')
        delivery_to = (datetime.utcnow() + timedelta(days=10)).strftime('%Y-%m-%d')
        order_from = (datetime.utcnow() - timedelta(days=1)).strftime('%Y-%m-%d')
        order_to = (datetime.utcnow() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        command = GetOrders(
            delivery_date_from=delivery_from,
            delivery_date_to=delivery_to,
            order_date_from=order_from,
            order_date_to=order_to
        )
        result = command.execute()
        
        assert len(result['orders']) >= 1
        assert any(o['id'] == sample_order.id for o in result['orders'])
    
    def test_get_orders_null_delivery_date_with_filter(self, db, sample_order):
        """Test órden con delivery_date NULL no aparece en filtros de delivery."""
        # Asegurar que delivery_date es NULL
        sample_order.delivery_date = None
        db.session.commit()
        
        # Filtrar por delivery_date
        date_from = datetime.utcnow().strftime('%Y-%m-%d')
        
        command = GetOrders(delivery_date_from=date_from)
        result = command.execute()
        
        # La orden con delivery_date NULL no debe aparecer
        assert not any(o['id'] == sample_order.id for o in result['orders'])
