import pytest
from decimal import Decimal
from datetime import datetime
from src.models.order import Order


class TestOrderModel:
    
    def test_create_order(self, db, sample_customer):
        order = Order(
            order_number='ORD-20251013-0001',
            customer_id=sample_customer.id,
            seller_id='SELLER-001',
            order_date=datetime.utcnow(),
            status='pending',
            subtotal=Decimal('100.00'),
            tax_amount=Decimal('19.00'),
            total_amount=Decimal('119.00')
        )
        db.session.add(order)
        db.session.commit()
        
        assert order.id is not None
        assert order.order_number == 'ORD-20251013-0001'
        assert order.status == 'pending'
    
    def test_order_defaults(self, db, sample_customer):
        order = Order(
            order_number='ORD-TEST',
            customer_id=sample_customer.id,
            seller_id='SELLER-002',
            subtotal=Decimal('50.00'),
            total_amount=Decimal('50.00')
        )
        db.session.add(order)
        db.session.commit()
        
        assert order.status == 'pending'
        assert order.discount_amount == Decimal('0.00')
        assert order.tax_amount == Decimal('0.00')
        assert order.created_at is not None
    
    def test_order_to_dict_basic(self, db, sample_order):
        result = sample_order.to_dict()
        
        assert result['order_number'] == sample_order.order_number
        assert result['status'] == 'pending'
        assert 'total_amount' in result
    
    def test_order_to_dict_with_items(self, db, sample_order):
        """Test to_dict with items included."""
        result = sample_order.to_dict(include_items=True)
        
        assert 'items' in result
        # sample_order ya tiene 2 items (JER-001 y VAC-001)
        assert len(result['items']) >= 2
        assert result['items'][0]['product_sku'] in ['JER-001', 'VAC-001']
    
    def test_order_to_dict_with_customer(self, db, sample_order):
        """Test to_dict with customer included."""
        result = sample_order.to_dict(include_customer=True)
        
        assert 'customer' in result
        assert result['customer']['business_name'] == sample_order.customer.business_name
    
    def test_order_relationship_with_customer(self, db, sample_order):
        """Test relationship with customer."""
        assert sample_order.customer is not None
        assert sample_order.customer.business_name == 'Hospital Test'
    
    def test_order_relationship_with_items(self, db, sample_order):
        """Test relationship with items."""
        items_list = list(sample_order.items)
        assert len(items_list) >= 2
