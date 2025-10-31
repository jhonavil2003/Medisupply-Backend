from src.websockets.websocket_manager import InventoryNotifier

@pytest.fixture
def mock_socketio(monkeypatch):
    fake_socketio = type("FakeSocketIO", (), {"emit": lambda *a, **kw: None})()
    monkeypatch.setattr("src.websockets.websocket_manager.socketio", fake_socketio)

def test_notify_stock_change_runs(mock_socketio):
    InventoryNotifier.notify_stock_change("TEST-001", {"product_sku": "TEST-001", "total_available": 10}, "update")

def test_notify_multiple_stock_changes(mock_socketio):
    changes = [
        {"product_sku": "SKU-1", "stock_data": {"product_sku": "SKU-1"}, "change_type": "update"},
        {"product_sku": "SKU-2", "stock_data": {"product_sku": "SKU-2"}, "change_type": "low_stock"}
    ]
    InventoryNotifier.notify_multiple_stock_changes(changes)

def test_notify_low_stock_alert(mock_socketio):
    InventoryNotifier.notify_low_stock_alert("SKU-1", {"product_sku": "SKU-1"})

def test_notify_out_of_stock(mock_socketio):
    InventoryNotifier.notify_out_of_stock("SKU-1", {"product_sku": "SKU-1"})

def test_notify_restock(mock_socketio):
    InventoryNotifier.notify_restock("SKU-1", {"product_sku": "SKU-1"})
