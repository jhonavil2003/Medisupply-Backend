import pytest
from decimal import Decimal
from src.models.inventory import Inventory


class TestInventoryModel:
    
    def test_create_inventory(self, db, sample_distribution_center):
        inventory = Inventory(
            product_sku='TEST-001',
            distribution_center_id=sample_distribution_center.id,
            quantity_available=100,
            quantity_reserved=10,
            unit_cost=Decimal('5.00')
        )
        db.session.add(inventory)
        db.session.commit()
        
        assert inventory.id is not None
        assert inventory.product_sku == 'TEST-001'
        assert inventory.quantity_available == 100
    
    def test_inventory_defaults(self, db, sample_distribution_center):
        inventory = Inventory(
            product_sku='DEF-001',
            distribution_center_id=sample_distribution_center.id
        )
        db.session.add(inventory)
        db.session.commit()
        
        assert inventory.quantity_available == 0
        assert inventory.quantity_reserved == 0
        assert inventory.quantity_in_transit == 0
        assert inventory.minimum_stock_level == 0
    
    def test_inventory_quantity_total(self, db, sample_inventory):
        assert sample_inventory.quantity_total == 115
    
    def test_inventory_is_low_stock(self, db, sample_distribution_center):
        inventory = Inventory(
            product_sku='LOW-001',
            distribution_center_id=sample_distribution_center.id,
            quantity_available=15,
            minimum_stock_level=20
        )
        db.session.add(inventory)
        db.session.commit()
        
        assert inventory.is_low_stock is True
    
    def test_inventory_is_out_of_stock(self, db, sample_distribution_center):
        inventory = Inventory(
            product_sku='OUT-001',
            distribution_center_id=sample_distribution_center.id,
            quantity_available=0
        )
        db.session.add(inventory)
        db.session.commit()
        
        assert inventory.is_out_of_stock is True
    
    def test_inventory_to_dict(self, db, sample_inventory):
        result = sample_inventory.to_dict()
        
        assert result['product_sku'] == 'JER-001'
        assert result['quantity_available'] == 100
        assert result['quantity_total'] == 115
        assert result['is_low_stock'] is False
    
    def test_inventory_to_dict_with_center(self, db, sample_inventory):
        result = sample_inventory.to_dict(include_center=True)
        
        assert 'distribution_center' in result
        assert result['distribution_center']['code'] == 'DC-001'
    
    def test_inventory_unique_constraint(self, db, sample_distribution_center):
        inv1 = Inventory(
            product_sku='DUP-001',
            distribution_center_id=sample_distribution_center.id,
            quantity_available=100
        )
        db.session.add(inv1)
        db.session.commit()
        
        inv2 = Inventory(
            product_sku='DUP-001',
            distribution_center_id=sample_distribution_center.id,
            quantity_available=50
        )
        db.session.add(inv2)
        
        with pytest.raises(Exception):
            db.session.commit()
