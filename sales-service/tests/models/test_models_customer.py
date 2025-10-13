import pytest
from decimal import Decimal
from src.models.customer import Customer


class TestCustomerModel:
    
    def test_create_customer(self, db):
        customer = Customer(
            document_type='NIT',
            document_number='123456789',
            business_name='Test Company',
            customer_type='hospital',
            city='Bogotá'
        )
        db.session.add(customer)
        db.session.commit()
        
        assert customer.id is not None
        assert customer.business_name == 'Test Company'
        assert customer.customer_type == 'hospital'
    
    def test_customer_defaults(self, db):
        customer = Customer(
            document_type='NIT',
            document_number='123456789',
            business_name='Test',
            customer_type='clinica',
            city='Medellín'
        )
        db.session.add(customer)
        db.session.commit()
        
        assert customer.is_active is True
        assert customer.credit_days == 0
        assert customer.created_at is not None
    
    def test_customer_to_dict(self, db, sample_customer):
        result = sample_customer.to_dict()
        
        assert 'id' in result
        assert result['business_name'] == sample_customer.business_name
        assert result['customer_type'] == sample_customer.customer_type
        assert result['is_active'] is True
    
    def test_customer_with_credit_limit(self, db):
        customer = Customer(
            document_type='NIT',
            document_number='987654321',
            business_name='Premium Hospital',
            customer_type='hospital',
            city='Cali',
            credit_limit=Decimal('5000000.00'),
            credit_days=60
        )
        db.session.add(customer)
        db.session.commit()
        
        assert customer.credit_limit == Decimal('5000000.00')
        assert customer.credit_days == 60
    
    def test_customer_unique_document(self, db):
        customer1 = Customer(
            document_type='NIT',
            document_number='UNIQUE-123',
            business_name='Company 1',
            customer_type='hospital',
            city='Bogotá'
        )
        db.session.add(customer1)
        db.session.commit()
        
        customer2 = Customer(
            document_type='NIT',
            document_number='UNIQUE-123',
            business_name='Company 2',
            customer_type='clinica',
            city='Medellín'
        )
        db.session.add(customer2)
        
        with pytest.raises(Exception):
            db.session.commit()
