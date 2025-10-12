import pytest
from src.main import create_app
from src.session import db as _db
from src.models.customer import Customer
from src.models.order import Order
from src.models.order_item import OrderItem


@pytest.fixture(scope='function')
def app():
    """Create and configure a test Flask application."""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
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
        credit_limit=50000000.00,
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
        credit_limit=30000000.00,
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
        subtotal=100000.00,
        discount_amount=5000.00,
        tax_amount=18050.00,
        total_amount=113050.00,
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
        unit_price=350.00,
        discount_percentage=5.0,
        tax_percentage=19.0,
        subtotal=33250.00,
        total=39567.50,
        distribution_center_code='DC-BOG-001',
        stock_confirmed=True
    )
    item1.calculate_totals()
    
    item2 = OrderItem(
        order_id=order.id,
        product_sku='VAC-001',
        product_name='Vacutainer',
        quantity=50,
        unit_price=1200.00,
        discount_percentage=0.0,
        tax_percentage=19.0,
        subtotal=60000.00,
        total=71400.00,
        distribution_center_code='DC-BOG-001',
        stock_confirmed=True
    )
    item2.calculate_totals()
    
    db.session.add(item1)
    db.session.add(item2)
    db.session.commit()
    
    return order
