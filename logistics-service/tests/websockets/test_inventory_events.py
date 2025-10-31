import pytest
from src.websockets.inventory_events import InventoryEvent, InventoryEventDetector

def test_inventory_event_to_dict():
    event = InventoryEvent("SKU-1", "update", 10, 20, 1, "DC-1")
    d = event.to_dict()
    assert d["product_sku"] == "SKU-1"
    assert d["change_type"] == "update"
    assert d["previous_quantity"] == 10
    assert d["new_quantity"] == 20
    assert d["distribution_center_id"] == 1

def test_detect_change_type_sale():
    t = InventoryEventDetector.detect_change_type(20, 10)
    assert t == "sale"

def test_should_notify_significant_change():
    assert InventoryEventDetector.should_notify(100, 80, 10.0) is True
    assert InventoryEventDetector.should_notify(100, 99, 10.0) is False


def test_track_inventory_change_not_significant(monkeypatch):
    from src.websockets.inventory_events import track_inventory_change
    monkeypatch.setattr("src.websockets.inventory_events.logger", type("FakeLogger", (), {"debug": lambda *a, **kw: None}))
    event = track_inventory_change("SKU-1", 100, 99, auto_publish=False)
    assert event is None

def test_track_inventory_change_auto_publish(monkeypatch):
    from src.websockets.inventory_events import track_inventory_change, InventoryEventPublisher
    monkeypatch.setattr(InventoryEventPublisher, "publish", lambda e: setattr(e, "published", True))
    event = track_inventory_change("SKU-1", 10, 0, auto_publish=True)
    assert hasattr(event, "published")

def test_inventory_event_publisher_publish(monkeypatch):
    from src.websockets.inventory_events import InventoryEventPublisher, InventoryEvent
    import src.websockets.websocket_manager as ws_manager
    import src.commands.get_stock_levels as stock_levels
    monkeypatch.setattr(ws_manager.InventoryNotifier, "notify_stock_change", lambda *a, **kw: None)
    monkeypatch.setattr(stock_levels.GetStockLevels, "execute", lambda self: {"total_available": 1, "total_reserved": 2, "total_in_transit": 3, "distribution_centers": []})
    event = InventoryEvent("SKU-1", "update", 10, 20, 1, "DC-1")
    InventoryEventPublisher.publish(event)

def test_inventory_event_publisher_publish_batch(monkeypatch):
    from src.websockets.inventory_events import InventoryEventPublisher, InventoryEvent
    monkeypatch.setattr(InventoryEventPublisher, "publish", lambda e: setattr(e, "published", True))
    events = [InventoryEvent("SKU-1", "update", 10, 20, 1, "DC-1"), InventoryEvent("SKU-2", "update", 5, 15, 2, "DC-2")]
    InventoryEventPublisher.publish_batch(events)
    for e in events:
        assert hasattr(e, "published")
