import pytest
import os
import sys
from datetime import datetime
from decimal import Decimal

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.main import create_app
from src.session import db as _db
from src.models.customer import Customer
from src.models.order import Order
from src.models.order_item import OrderItem

# Import visit entities
from src.entities.visit import Visit
from src.entities.salesperson import Salesperson
from src.entities.visit_status import VisitStatus
from src.entities.visit_file import VisitFile


@pytest.fixture(scope='function')
def app():
    """Create and configure a test Flask application."""
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
    """Provide test database session."""
    return _db


@pytest.fixture(scope='function')
def client(app):
    """Provide test client."""
    return app.test_client()


@pytest.fixture(scope='function')
def sample_customer(db):
    """Create a sample customer for testing."""
    customer = Customer(
        document_type='NIT',
        document_number='900123456-1',
        business_name='Hospital Test',
        trade_name='Hospital Test',
        customer_type='hospital',
        contact_name='Test Contact',
        contact_email='test@hospital.com',
        contact_phone='+57 1 1234567',
        address='Test Address 123',
        city='Bogotá',
        department='Cundinamarca',
        country='Colombia',
        credit_limit=Decimal('50000000.00'),
        credit_days=60,
        is_active=True
    )
    db.session.add(customer)
    db.session.commit()
    return customer


@pytest.fixture(scope='function')
def sample_customer_2(db):
    """Create a second sample customer for testing."""
    customer = Customer(
        document_type='NIT',
        document_number='800234567-2',
        business_name='Clínica Test',
        trade_name='Clínica Test',
        customer_type='clinica',
        contact_name='Test Contact 2',
        contact_email='test@clinica.com',
        contact_phone='+57 1 7654321',
        address='Test Address 456',
        city='Medellín',
        department='Antioquia',
        country='Colombia',
        credit_limit=Decimal('30000000.00'),
        credit_days=45,
        is_active=True
    )
    db.session.add(customer)
    db.session.commit()
    return customer


@pytest.fixture(scope='function')
def sample_order(db, sample_customer):
    """Create a sample order for testing."""
    order = Order(
        order_number='ORD-20251011-0001',
        customer_id=sample_customer.id,
        seller_id='SELLER-001',
        seller_name='Test Seller',
        status='pending',
        subtotal=Decimal('100000.00'),
        discount_amount=Decimal('5000.00'),
        tax_amount=Decimal('18050.00'),
        total_amount=Decimal('113050.00'),
        payment_terms='credito_30',
        payment_method='transferencia',
        delivery_address=sample_customer.address,
        delivery_city=sample_customer.city,
        delivery_department=sample_customer.department,
        notes='Test order'
    )
    db.session.add(order)
    db.session.commit()
    
    # Add order items
    item1 = OrderItem(
        order_id=order.id,
        product_sku='JER-001',
        product_name='Jeringa desechable 3ml',
        quantity=100,
        unit_price=Decimal('350.00'),
        discount_percentage=Decimal('5.0'),
        discount_amount=Decimal('1750.00'),
        tax_percentage=Decimal('19.0'),
        tax_amount=Decimal('6314.50'),
        subtotal=Decimal('33250.00'),
        total=Decimal('39564.50'),
        distribution_center_code='DC-BOG-001',
        stock_confirmed=True
    )
    
    item2 = OrderItem(
        order_id=order.id,
        product_sku='VAC-001',
        product_name='Vacutainer',
        quantity=50,
        unit_price=Decimal('1200.00'),
        discount_percentage=Decimal('0.0'),
        discount_amount=Decimal('0.00'),
        tax_percentage=Decimal('19.0'),
        tax_amount=Decimal('11400.00'),
        subtotal=Decimal('60000.00'),
        total=Decimal('71400.00'),
        distribution_center_code='DC-BOG-001',
        stock_confirmed=True
    )
    
    db.session.add(item1)
    db.session.add(item2)
    db.session.commit()
    
    return order


@pytest.fixture(scope='function')
def sample_order_item(db, sample_order):
    """Create a sample order item for testing."""
    item = OrderItem(
        order_id=sample_order.id,
        product_sku='TEST-001',
        product_name='Test Product',
        quantity=10,
        unit_price=Decimal('1000.00'),
        discount_percentage=Decimal('5.0'),
        discount_amount=Decimal('500.00'),
        tax_percentage=Decimal('19.0'),
        tax_amount=Decimal('1805.00'),
        subtotal=Decimal('9500.00'),
        total=Decimal('11305.00'),
        distribution_center_code='DC-TEST-001',
        stock_confirmed=True
    )
    db.session.add(item)
    db.session.commit()
    return item


@pytest.fixture(scope='function')
def multiple_customers(db):
    """Create multiple customers for testing."""
    customers = [
        Customer(
            document_type='NIT',
            document_number='900111111-1',
            business_name='Hospital San José',
            trade_name='Hospital San José',
            customer_type='hospital',
            contact_name='Contact 1',
            contact_email='contact1@hospital.com',
            contact_phone='+57 1 1111111',
            address='Address 1',
            city='Bogotá',
            department='Cundinamarca',
            country='Colombia',
            credit_limit=100000000.00,
            credit_days=60,
            is_active=True
        ),
        Customer(
            document_type='NIT',
            document_number='900222222-2',
            business_name='Clínica El Rosario',
            trade_name='Clínica El Rosario',
            customer_type='clinica',
            contact_name='Contact 2',
            contact_email='contact2@clinica.com',
            contact_phone='+57 2 2222222',
            address='Address 2',
            city='Medellín',
            department='Antioquia',
            country='Colombia',
            credit_limit=50000000.00,
            credit_days=45,
            is_active=True
        ),
        Customer(
            document_type='NIT',
            document_number='900333333-3',
            business_name='Farmacia Test',
            trade_name='Farmacia Test',
            customer_type='farmacia',
            contact_name='Contact 3',
            contact_email='contact3@farmacia.com',
            contact_phone='+57 3 3333333',
            address='Address 3',
            city='Cali',
            department='Valle del Cauca',
            country='Colombia',
            credit_limit=20000000.00,
            credit_days=30,
            is_active=False
        )
    ]
    
    for customer in customers:
        db.session.add(customer)
    
    db.session.commit()
    return customers


@pytest.fixture(scope='function')
def multiple_orders(db, sample_customer, sample_customer_2):
    """Create multiple orders for testing."""
    orders = []
    
    # Order 1 - Pending
    order1 = Order(
        order_number='ORD-20251013-0001',
        customer_id=sample_customer.id,
        seller_id='SELLER-001',
        seller_name='Seller 1',
        status='pending',
        subtotal=Decimal('100000.00'),
        discount_amount=Decimal('5000.00'),
        tax_amount=Decimal('18050.00'),
        total_amount=Decimal('113050.00'),
        payment_terms='credito_30',
        payment_method='transferencia'
    )
    db.session.add(order1)
    db.session.flush()
    
    item1 = OrderItem(
        order_id=order1.id,
        product_sku='JER-001',
        product_name='Jeringa 3ml',
        quantity=100,
        unit_price=Decimal('1000.00'),
        discount_percentage=Decimal('5.0'),
        discount_amount=Decimal('5000.00'),
        tax_percentage=Decimal('19.0'),
        tax_amount=Decimal('18050.00'),
        subtotal=Decimal('95000.00'),
        total=Decimal('113050.00'),
        distribution_center_code='DC-001',
        stock_confirmed=True
    )
    db.session.add(item1)
    orders.append(order1)
    
    # Order 2 - Confirmed
    order2 = Order(
        order_number='ORD-20251013-0002',
        customer_id=sample_customer_2.id,
        seller_id='SELLER-002',
        seller_name='Seller 2',
        status='confirmed',
        subtotal=Decimal('50000.00'),
        discount_amount=Decimal('0.00'),
        tax_amount=Decimal('9500.00'),
        total_amount=Decimal('59500.00'),
        payment_terms='credito_45',
        payment_method='credito'
    )
    db.session.add(order2)
    db.session.flush()
    
    item2 = OrderItem(
        order_id=order2.id,
        product_sku='VAC-001',
        product_name='Vacutainer',
        quantity=50,
        unit_price=Decimal('1000.00'),
        discount_percentage=Decimal('0.0'),
        discount_amount=Decimal('0.00'),
        tax_percentage=Decimal('19.0'),
        tax_amount=Decimal('9500.00'),
        subtotal=Decimal('50000.00'),
        total=Decimal('59500.00'),
        distribution_center_code='DC-002',
        stock_confirmed=True
    )
    db.session.add(item2)
    orders.append(order2)
    
    db.session.commit()
    return orders


# Visit-related fixtures
@pytest.fixture(scope='function')
def sample_salesperson(db):
    """Create a sample salesperson for testing."""
    from datetime import date
    salesperson = Salesperson(
        employee_id='SELLER-001',
        first_name='Juan',
        last_name='Pérez',
        email='juan.perez@medisupply.com',
        phone='+57 300 1234567',
        territory='Bogotá Norte',
        hire_date=date(2023, 1, 15),
        is_active=True
    )
    db.session.add(salesperson)
    db.session.commit()
    return salesperson


@pytest.fixture(scope='function')
def sample_salesperson_2(db):
    """Create a second sample salesperson for testing."""
    from datetime import date
    salesperson = Salesperson(
        employee_id='SELLER-002',
        first_name='María',
        last_name='González',
        email='maria.gonzalez@medisupply.com',
        phone='+57 300 7654321',
        territory='Medellín Centro',
        hire_date=date(2023, 3, 10),
        is_active=True
    )
    db.session.add(salesperson)
    db.session.commit()
    return salesperson


@pytest.fixture(scope='function')
def sample_visit(db, sample_customer, sample_salesperson):
    """Create a sample visit for testing."""
    from datetime import date, time
    from decimal import Decimal
    
    visit = Visit(
        customer_id=sample_customer.id,
        salesperson_id=sample_salesperson.id,
        visit_date=date(2025, 11, 15),
        visit_time=time(10, 30),
        contacted_persons='Dr. Juan Pérez, Jefe de Compras',
        clinical_findings='Necesitan reposición de inventario médico',
        additional_notes='Cliente interesado en productos ortopédicos',
        address='Calle 10 #5-25, Bogotá',
        latitude=Decimal('4.60971'),
        longitude=Decimal('-74.08175'),
        status=VisitStatus.PROGRAMADA
    )
    db.session.add(visit)
    db.session.commit()
    return visit


@pytest.fixture(scope='function')
def sample_visit_file(db, sample_visit):
    """Create a sample visit file for testing."""
    visit_file = VisitFile(
        visit_id=sample_visit.id,
        file_name='test_document.pdf',
        file_path='/uploads/visits/1/test_document_20251101_100000_abc123.pdf',
        file_size=1024000,  # 1MB
        mime_type='application/pdf'
    )
    db.session.add(visit_file)
    db.session.commit()
    return visit_file


@pytest.fixture(scope='function')
def multiple_visits(db, sample_customer, sample_customer_2, sample_salesperson, sample_salesperson_2):
    """Create multiple visits for testing."""
    from datetime import date, time
    from decimal import Decimal
    
    visits = []
    
    # Visit 1 - PROGRAMADA
    visit1 = Visit(
        customer_id=sample_customer.id,
        salesperson_id=sample_salesperson.id,
        visit_date=date(2025, 11, 10),
        visit_time=time(9, 0),
        contacted_persons='Dr. Ana López',
        clinical_findings='Revisión rutinaria',
        additional_notes='Primera visita del mes',
        address='Dirección 1',
        latitude=Decimal('4.60971'),
        longitude=Decimal('-74.08175'),
        status=VisitStatus.PROGRAMADA
    )
    db.session.add(visit1)
    visits.append(visit1)
    
    # Visit 2 - COMPLETADA
    visit2 = Visit(
        customer_id=sample_customer_2.id,
        salesperson_id=sample_salesperson_2.id,
        visit_date=date(2025, 11, 8),
        visit_time=time(14, 30),
        contacted_persons='Dr. Carlos Ruiz',
        clinical_findings='Inventario completo',
        additional_notes='Visita exitosa',
        address='Dirección 2',
        latitude=Decimal('6.25184'),
        longitude=Decimal('-75.56359'),
        status=VisitStatus.COMPLETADA
    )
    db.session.add(visit2)
    visits.append(visit2)
    
    # Visit 3 - ELIMINADA
    visit3 = Visit(
        customer_id=sample_customer.id,
        salesperson_id=sample_salesperson.id,
        visit_date=date(2025, 11, 5),
        visit_time=time(11, 0),
        contacted_persons='Dr. Luis Martín',
        clinical_findings='Visita cancelada',
        additional_notes='Cliente no disponible',
        address='Dirección 3',
        status=VisitStatus.ELIMINADA
    )
    db.session.add(visit3)
    visits.append(visit3)
    
    db.session.commit()
    return visits


@pytest.fixture(scope='function')
def multiple_salespersons(db):
    """Create multiple salespersons for testing."""
    from datetime import date
    
    salespersons = [
        Salesperson(
            employee_id='SELLER-100',
            first_name='Pedro',
            last_name='Ramírez',
            email='pedro.ramirez@medisupply.com',
            phone='+57 301 1111111',
            territory='Bogotá Sur',
            hire_date=date(2022, 6, 1),
            is_active=True
        ),
        Salesperson(
            employee_id='SELLER-101',
            first_name='Ana',
            last_name='Torres',
            email='ana.torres@medisupply.com',
            phone='+57 302 2222222',
            territory='Cali Norte',
            hire_date=date(2023, 8, 15),
            is_active=True
        ),
        Salesperson(
            employee_id='SELLER-102',
            first_name='Carlos',
            last_name='Mendoza',
            email='carlos.mendoza@medisupply.com',
            phone='+57 303 3333333',
            territory='Barranquilla',
            hire_date=date(2021, 2, 20),
            is_active=False
        )
    ]
    
    for salesperson in salespersons:
        db.session.add(salesperson)
    
    db.session.commit()
    return salespersons
