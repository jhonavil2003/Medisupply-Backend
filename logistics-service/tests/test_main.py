from src.main import create_app

def test_create_app_returns_flask():
    app_obj = create_app(config={
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False
    })
    if isinstance(app_obj, tuple):
        app = app_obj[0]
    else:
        app = app_obj
    assert hasattr(app, 'route')
