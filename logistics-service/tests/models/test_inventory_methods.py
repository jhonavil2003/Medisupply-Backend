from src.models.inventory import Inventory

def test_update_quantity_available():
    inv = Inventory(product_sku="SKU-1", quantity_available=10)
    inv.update_quantity_available(20, auto_notify=False)
    assert inv.quantity_available == 20
