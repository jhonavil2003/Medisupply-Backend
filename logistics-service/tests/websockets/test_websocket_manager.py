import pytest
from src.websockets.websocket_manager import InventoryNotifier

def test_notify_stock_change_runs(monkeypatch):
    monkeypatch.setattr("src.websockets.websocket_manager.socketio", type("FakeSocketIO", (), {"emit": lambda *a, **kw: None}))
    InventoryNotifier.notify_stock_change("TEST-001", {"product_sku": "TEST-001", "total_available": 10}, "update")


def test_notify_multiple_stock_changes(monkeypatch):
    monkeypatch.setattr("src.websockets.websocket_manager.socketio", type("FakeSocketIO", (), {"emit": lambda *a, **kw: None}))
    changes = [
        {"product_sku": "SKU-1", "stock_data": {"product_sku": "SKU-1"}, "change_type": "update"},
        {"product_sku": "SKU-2", "stock_data": {"product_sku": "SKU-2"}, "change_type": "low_stock"}
    ]
    InventoryNotifier.notify_multiple_stock_changes(changes)

def test_notify_low_stock_alert(monkeypatch):
    monkeypatch.setattr("src.websockets.websocket_manager.socketio", type("FakeSocketIO", (), {"emit": lambda *a, **kw: None}))
    InventoryNotifier.notify_low_stock_alert("SKU-1", {"product_sku": "SKU-1"})

def test_notify_out_of_stock(monkeypatch):
    monkeypatch.setattr("src.websockets.websocket_manager.socketio", type("FakeSocketIO", (), {"emit": lambda *a, **kw: None}))
    InventoryNotifier.notify_out_of_stock("SKU-1", {"product_sku": "SKU-1"})

def test_notify_restock(monkeypatch):
    monkeypatch.setattr("src.websockets.websocket_manager.socketio", type("FakeSocketIO", (), {"emit": lambda *a, **kw: None}))
    InventoryNotifier.notify_restock("SKU-1", {"product_sku": "SKU-1"})
