import pytest
import os
import sys
from datetime import datetime, date
from decimal import Decimal

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.main import create_app
from src.session import db as _db
from src.models.product import Product
from src.models.supplier import Supplier
from src.models.certification import Certification
from src.models.regulatory_condition import RegulatoryCondition


@pytest.fixture(scope='function')
def app():
    config = {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False
    }
    
    app = create_app(config=config)
    
    with app.app_context():
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture(scope='function')
def db(app):
    with app.app_context():
        yield _db
        _db.session.remove()


@pytest.fixture(scope='function')
def client(app, db):
    return app.test_client()


@pytest.fixture
def sample_supplier(db):
    supplier = Supplier(
        name='MedSupply Inc',
        legal_name='MedSupply Incorporated',
        tax_id='123456789',
        email='contact@medsupply.com',
        phone='+1-555-0100',
        website='https://medsupply.com',
        address_line1='123 Medical Drive',
        city='New York',
        state='NY',
        country='USA',
        postal_code='10001',
        payment_terms='Net 30',
        credit_limit=Decimal('50000.00'),
        currency='USD',
        is_certified=True,
        is_active=True
    )
    db.session.add(supplier)
    db.session.flush()
    return supplier


@pytest.fixture
def sample_product(db, sample_supplier):
    product = Product(
        sku='TEST-001',
        name='Test Product',
        description='Test product description',
        category='Medical Equipment',
        subcategory='Diagnostic',
        unit_price=Decimal('99.99'),
        currency='USD',
        unit_of_measure='unit',
        supplier_id=sample_supplier.id,
        requires_cold_chain=False,
        storage_temperature_min=Decimal('15.00'),
        storage_temperature_max=Decimal('25.00'),
        storage_humidity_max=Decimal('60.00'),
        sanitary_registration='REG-123456',
        requires_prescription=False,
        regulatory_class='Class II',
        weight_kg=Decimal('0.5'),
        length_cm=Decimal('10.0'),
        width_cm=Decimal('5.0'),
        height_cm=Decimal('3.0'),
        is_active=True,
        is_discontinued=False,
        manufacturer='Test Manufacturer',
        country_of_origin='USA',
        barcode='1234567890123'
    )
    db.session.add(product)
    db.session.flush()
    return product


@pytest.fixture
def sample_certification(db, sample_product):
    certification = Certification(
        product_id=sample_product.id,
        certification_type='FDA',
        certification_number='FDA-123456',
        issuing_authority='US Food and Drug Administration',
        country='USA',
        issue_date=date(2023, 1, 1),
        expiry_date=date(2025, 12, 31),
        is_valid=True,
        certificate_url='https://example.com/cert.pdf'
    )
    db.session.add(certification)
    db.session.flush()
    return certification


@pytest.fixture
def sample_regulatory_condition(db, sample_product):
    condition = RegulatoryCondition(
        product_id=sample_product.id,
        country='Colombia',
        regulatory_body='INVIMA',
        import_restrictions='Requires import license',
        special_handling_requirements='Temperature controlled',
        distribution_restrictions='Licensed distributors only',
        required_documentation='Certificate of Analysis, Import License',
        is_approved_for_sale=True,
        approval_date=date(2023, 6, 15)
    )
    db.session.add(condition)
    db.session.flush()
    return condition


@pytest.fixture
def multiple_products(db, sample_supplier):
    products = [
        Product(
            sku='JER-001',
            name='Jeringa desechable 3ml',
            description='Jeringa estéril de un solo uso',
            category='Instrumental',
            subcategory='Jeringas',
            unit_price=Decimal('0.50'),
            currency='USD',
            unit_of_measure='unidad',
            supplier_id=sample_supplier.id,
            requires_cold_chain=False,
            is_active=True,
            manufacturer='PharmaTech',
            country_of_origin='USA',
            barcode='7501234567890'
        ),
        Product(
            sku='GUANTE-001',
            name='Guantes de látex',
            description='Guantes de examinación',
            category='Protección Personal',
            subcategory='Guantes',
            unit_price=Decimal('12.50'),
            currency='USD',
            unit_of_measure='caja',
            supplier_id=sample_supplier.id,
            requires_cold_chain=False,
            is_active=True,
            manufacturer='SafeGuard',
            country_of_origin='China',
            barcode='7501234567891'
        ),
        Product(
            sku='VAC-001',
            name='Vacuna COVID-19',
            description='Vacuna contra coronavirus',
            category='Medicamentos',
            subcategory='Vacunas',
            unit_price=Decimal('45.00'),
            currency='USD',
            unit_of_measure='dosis',
            supplier_id=sample_supplier.id,
            requires_cold_chain=True,
            storage_temperature_min=Decimal('-70.00'),
            storage_temperature_max=Decimal('-60.00'),
            is_active=True,
            manufacturer='BioPharm',
            country_of_origin='USA',
            barcode='7501234567892'
        ),
        Product(
            sku='INACTIVE-001',
            name='Producto Inactivo',
            description='Este producto está inactivo',
            category='Test',
            subcategory='Test',
            unit_price=Decimal('10.00'),
            currency='USD',
            unit_of_measure='unidad',
            supplier_id=sample_supplier.id,
            requires_cold_chain=False,
            is_active=False,
            manufacturer='Test',
            country_of_origin='USA',
            barcode='7501234567893'
        ),
    ]
    
    for product in products:
        db.session.add(product)
    db.session.flush()
    
    return products
