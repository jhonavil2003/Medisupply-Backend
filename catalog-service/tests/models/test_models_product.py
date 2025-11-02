import pytest
from decimal import Decimal
from src.models.product import Product


class TestProductModel:
    
    def test_create_product(self, db, sample_supplier):
        product = Product(
            sku='TEST-123',
            name='Test Product',
            description='Test description',
            category='Medical',
            unit_price=Decimal('10.00'),
            unit_of_measure='unit',
            supplier_id=sample_supplier.id
        )
        db.session.add(product)
        db.session.commit()
        
        assert product.id is not None
        assert product.sku == 'TEST-123'
        assert product.name == 'Test Product'
        assert product.unit_price == Decimal('10.00')
    
    def test_product_defaults(self, db, sample_supplier):
        product = Product(
            sku='TEST-DEF',
            name='Default Test',
            category='Test',
            unit_price=Decimal('5.00'),
            unit_of_measure='unit',
            supplier_id=sample_supplier.id
        )
        db.session.add(product)
        db.session.commit()
        
        assert product.currency == 'USD'
        assert product.requires_cold_chain is False
        assert product.is_active is True
        assert product.created_at is not None
    
    def test_product_relationship_with_supplier(self, db, sample_product, sample_supplier):
        assert sample_product.supplier is not None
        assert sample_product.supplier.id == sample_supplier.id
    
    def test_product_to_dict(self, db, sample_product):
        result = sample_product.to_dict()
        
        assert result['sku'] == 'TEST-001'
        assert result['name'] == 'Test Product'
        assert result['category'] == 'Medical Equipment'
        assert 'storage_conditions' in result
        assert 'regulatory_info' in result
        assert 'physical_dimensions' in result
    
    def test_product_to_dict_detailed(self, db, sample_product, sample_certification, sample_regulatory_condition):
        result = sample_product.to_dict_detailed()
        
        assert 'certifications' in result
        assert 'regulatory_conditions' in result
        assert len(result['certifications']) == 1
        assert len(result['regulatory_conditions']) == 1
    
    def test_product_unique_sku_constraint(self, db, sample_supplier):
        product1 = Product(
            sku='UNIQUE-001',
            name='Product 1',
            category='Test',
            unit_price=Decimal('10.00'),
            unit_of_measure='unit',
            supplier_id=sample_supplier.id
        )
        db.session.add(product1)
        db.session.commit()
        
        product2 = Product(
            sku='UNIQUE-001',
            name='Product 2',
            category='Test',
            unit_price=Decimal('20.00'),
            unit_of_measure='unit',
            supplier_id=sample_supplier.id
        )
        db.session.add(product2)
        
        with pytest.raises(Exception):
            db.session.commit()
    
    def test_product_cascade_delete_certifications(self, db, sample_product, sample_certification):
        from src.models.certification import Certification
        
        cert_id = sample_certification.id
        db.session.delete(sample_product)
        db.session.commit()
        
        deleted_cert = Certification.query.get(cert_id)
        assert deleted_cert is None
    
    def test_product_cascade_delete_regulatory_conditions(self, db, sample_product, sample_regulatory_condition):
        from src.models.regulatory_condition import RegulatoryCondition
        
        condition_id = sample_regulatory_condition.id
        db.session.delete(sample_product)
        db.session.commit()
        
        deleted_condition = RegulatoryCondition.query.get(condition_id)
        assert deleted_condition is None

    def test_product_repr(self, db, sample_product):
        """Test that Product __repr__ method works correctly"""
        repr_str = repr(sample_product)
        
        assert 'Product TEST-001: Test Product' in repr_str
        assert sample_product.sku in repr_str
        assert sample_product.name in repr_str
