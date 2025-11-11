import pytest
from datetime import date
from decimal import Decimal
from src.models.supplier import Supplier
from src.models.certification import Certification
from src.models.regulatory_condition import RegulatoryCondition


class TestSupplierModel:
    
    def test_create_supplier(self, db):
        supplier = Supplier(
            name='Test Supplier',
            legal_name='Test Supplier LLC',
            tax_id='987654321',
            country='USA'
        )
        db.session.add(supplier)
        db.session.commit()
        
        assert supplier.id is not None
        assert supplier.name == 'Test Supplier'
        assert supplier.tax_id == '987654321'
    
    def test_supplier_defaults(self, db):
        supplier = Supplier(
            name='Default Supplier',
            legal_name='Default Supplier Inc',
            tax_id='111222333',
            country='USA'
        )
        db.session.add(supplier)
        db.session.commit()
        
        assert supplier.currency is None  # Currency no longer has USD default
        assert supplier.is_certified is False
        assert supplier.is_active is True
    
    def test_supplier_to_dict(self, db, sample_supplier):
        result = sample_supplier.to_dict()
        
        assert result['name'] == 'MedSupply Inc'
        assert result['tax_id'] == '123456789'
        assert 'address' in result
        assert result['address']['city'] == 'New York'
    
    def test_supplier_unique_tax_id(self, db):
        supplier1 = Supplier(
            name='Supplier 1',
            legal_name='Supplier One LLC',
            tax_id='UNIQUE123',
            country='USA'
        )
        db.session.add(supplier1)
        db.session.commit()
        
        supplier2 = Supplier(
            name='Supplier 2',
            legal_name='Supplier Two LLC',
            tax_id='UNIQUE123',
            country='USA'
        )
        db.session.add(supplier2)
        
        with pytest.raises(Exception):
            db.session.commit()
    
    def test_supplier_products_relationship(self, db, sample_supplier, sample_product):
        products = sample_supplier.products.all()
        assert len(products) == 1
        assert products[0].id == sample_product.id


class TestCertificationModel:
    
    def test_create_certification(self, db, sample_product):
        cert = Certification(
            product_id=sample_product.id,
            certification_type='CE',
            certification_number='CE-789012',
            issuing_authority='European Commission',
            country='EU',
            issue_date=date(2023, 3, 15),
            expiry_date=date(2026, 3, 14),
            is_valid=True
        )
        db.session.add(cert)
        db.session.commit()
        
        assert cert.id is not None
        assert cert.certification_type == 'CE'
    
    def test_certification_to_dict(self, db, sample_certification):
        result = sample_certification.to_dict()
        
        assert result['certification_type'] == 'FDA'
        assert result['certification_number'] == 'FDA-123456'
        assert result['country'] == 'USA'


class TestRegulatoryConditionModel:
    
    def test_create_regulatory_condition(self, db, sample_product):
        condition = RegulatoryCondition(
            product_id=sample_product.id,
            country='Mexico',
            regulatory_body='COFEPRIS',
            import_restrictions='Requires import permit',
            is_approved_for_sale=True,
            approval_date=date(2023, 5, 20)
        )
        db.session.add(condition)
        db.session.commit()
        
        assert condition.id is not None
        assert condition.country == 'Mexico'
    
    def test_regulatory_condition_to_dict(self, db, sample_regulatory_condition):
        result = sample_regulatory_condition.to_dict()
        
        assert result['country'] == 'Colombia'
        assert result['regulatory_body'] == 'INVIMA'
        assert result['is_approved_for_sale'] is True
