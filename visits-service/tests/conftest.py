import os
import pytest
from src.main import create_app
from src.session import db


@pytest.fixture(scope='session')
def app():
    """Create application for the tests."""
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False
    })
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture(scope='function')
def client(app):
    """Create a test client for the app."""
    return app.test_client()


@pytest.fixture(scope='function')
def db_session(app):
    """Create a database session for the test."""
    with app.app_context():
        yield db.session
        db.session.rollback()
        db.session.remove()