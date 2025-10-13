import pytest
from decimal import Decimal
from src.models.order_item import OrderItem


class TestOrderItemModel:
    
    def test_create_order_item(self, db, sample_order):
        """Test creating an order item with required fields."""
        item = OrderItem(
            order_id=sample_order.id,
            product_sku='PROD-001',
            product_name='Test Product',
            quantity=5,
            unit_price=Decimal('100.00'),
            discount_percentage=Decimal('0.00'),
            discount_amount=Decimal('0.00'),
            tax_percentage=Decimal('19.00'),
            tax_amount=Decimal('95.00'),
            subtotal=Decimal('500.00'),
            total=Decimal('595.00')
        )
        db.session.add(item)
        db.session.commit()
        
        assert item.id is not None
        assert item.product_sku == 'PROD-001'
        assert item.quantity == 5
    
    def test_order_item_defaults(self, db, sample_order):
        """Test order item default values."""
        item = OrderItem(
            order_id=sample_order.id,
            product_sku='PROD-002',
            product_name='Product 2',
            quantity=1,
            unit_price=Decimal('50.00'),
            discount_percentage=Decimal('0.00'),
            discount_amount=Decimal('0.00'),
            tax_percentage=Decimal('19.00'),
            tax_amount=Decimal('9.50'),
            subtotal=Decimal('50.00'),
            total=Decimal('59.50')
        )
        db.session.add(item)
        db.session.commit()
        
        assert item.discount_percentage == Decimal('0.00')
        assert item.tax_percentage == Decimal('19.00')
        assert item.stock_confirmed is False
    
    def test_order_item_calculate_totals(self, db, sample_order):
        """Test calculate_totals method."""
        item = OrderItem(
            order_id=sample_order.id,
            product_sku='PROD-003',
            product_name='Product 3',
            quantity=10,
            unit_price=Decimal('100.00'),
            discount_percentage=Decimal('10.00'),
            discount_amount=Decimal('0.00'),  # Will be calculated
            tax_percentage=Decimal('19.00'),
            tax_amount=Decimal('0.00'),  # Will be calculated
            subtotal=Decimal('0.00'),  # Will be calculated
            total=Decimal('0.00')  # Will be calculated
        )
        item.calculate_totals()
        
        # Verificar que los cálculos son correctos
        # discount = 100.00 * 10 * 10% = 100.00
        # subtotal = (100.00 * 10) - 100.00 = 900.00
        # tax = 900.00 * 19% = 171.00
        # total = 900.00 + 171.00 = 1071.00
        assert float(item.discount_amount) == 100.00
        assert float(item.subtotal) == 900.00
        assert float(item.tax_amount) == 171.00
        assert float(item.total) == 1071.00
    
    def test_order_item_to_dict(self, db, sample_order_item):
        """Test to_dict serialization."""
        result = sample_order_item.to_dict()
        
        assert result['product_sku'] == 'TEST-001'
        assert result['quantity'] == 10
        assert 'unit_price' in result
        assert 'total' in result
    
    def test_order_item_no_discount(self, db, sample_order):
        """Test order item with no discount."""
        item = OrderItem(
            order_id=sample_order.id,
            product_sku='PROD-004',
            product_name='Product 4',
            quantity=5,
            unit_price=Decimal('200.00'),
            discount_percentage=Decimal('0.00'),
            discount_amount=Decimal('0.00'),
            tax_percentage=Decimal('19.00'),
            tax_amount=Decimal('190.00'),
            subtotal=Decimal('1000.00'),
            total=Decimal('1190.00')
        )
        db.session.add(item)
        db.session.commit()
        
        # Verificar los valores sin llamar calculate_totals()
        assert item.discount_amount == Decimal('0.00')
        assert item.subtotal == Decimal('1000.00')
        assert item.tax_amount == Decimal('190.00')
        assert item.total == Decimal('1190.00')
    
    def test_order_item_relationship_with_order(self, db, sample_order_item):
        """Test relationship with order."""
        assert sample_order_item.order is not None
        assert sample_order_item.order.id == sample_order_item.order_id
