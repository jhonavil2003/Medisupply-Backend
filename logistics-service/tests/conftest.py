import pytest
import os
import sys
from datetime import datetime, date
from decimal import Decimal

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.main import create_app
from src.session import db as _db
from src.models.inventory import Inventory
from src.models.distribution_center import DistributionCenter


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


@pytest.fixture(scope='function')
def client(app):
    return app.test_client()


@pytest.fixture
def sample_distribution_center(db):
    dc = DistributionCenter(
        code='DC-001',
        name='Centro Bogotá',
        city='Bogotá',
        country='Colombia',
        is_active=True,
        supports_cold_chain=True
    )
    db.session.add(dc)
    db.session.commit()
    return dc


@pytest.fixture
def sample_distribution_center_2(db):
    dc = DistributionCenter(
        code='DC-002',
        name='Centro Medellín',
        city='Medellín',
        country='Colombia',
        is_active=True,
        supports_cold_chain=False
    )
    db.session.add(dc)
    db.session.commit()
    return dc


@pytest.fixture
def sample_inventory(db, sample_distribution_center):
    inventory = Inventory(
        product_sku='JER-001',
        distribution_center_id=sample_distribution_center.id,
        quantity_available=100,
        quantity_reserved=10,
        quantity_in_transit=5,
        minimum_stock_level=20,
        unit_cost=Decimal('2.50')
    )
    db.session.add(inventory)
    db.session.commit()
    return inventory


@pytest.fixture
def multiple_inventory_items(db, sample_distribution_center, sample_distribution_center_2):
    items = [
        Inventory(
            product_sku='JER-001',
            distribution_center_id=sample_distribution_center.id,
            quantity_available=100,
            quantity_reserved=10,
            quantity_in_transit=5,
            minimum_stock_level=20
        ),
        Inventory(
            product_sku='JER-001',
            distribution_center_id=sample_distribution_center_2.id,
            quantity_available=50,
            quantity_reserved=5,
            quantity_in_transit=0,
            minimum_stock_level=20
        ),
        Inventory(
            product_sku='VAC-001',
            distribution_center_id=sample_distribution_center.id,
            quantity_available=30,
            quantity_reserved=0,
            quantity_in_transit=10,
            minimum_stock_level=10
        ),
        Inventory(
            product_sku='GUANTE-001',
            distribution_center_id=sample_distribution_center.id,
            quantity_available=0,
            quantity_reserved=0,
            quantity_in_transit=0,
            minimum_stock_level=50
        )
    ]
    
    for item in items:
        db.session.add(item)
    
    db.session.commit()
    return items
