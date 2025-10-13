import pytest
from decimal import Decimal
from src.models.distribution_center import DistributionCenter


class TestDistributionCenterModel:
    
    def test_create_distribution_center(self, db):
        dc = DistributionCenter(
            code='DC-TEST',
            name='Centro Test',
            city='Test City',
            country='Test Country'
        )
        db.session.add(dc)
        db.session.commit()
        
        assert dc.id is not None
        assert dc.code == 'DC-TEST'
        assert dc.name == 'Centro Test'
    
    def test_distribution_center_defaults(self, db):
        dc = DistributionCenter(
            code='DC-DEF',
            name='Default Center',
            city='City',
            country='Country'
        )
        db.session.add(dc)
        db.session.commit()
        
        assert dc.is_active is True
        assert dc.supports_cold_chain is False
        assert dc.created_at is not None
    
    def test_distribution_center_to_dict(self, db, sample_distribution_center):
        result = sample_distribution_center.to_dict()
        
        assert result['code'] == 'DC-001'
        assert result['name'] == 'Centro Bogotá'
        assert result['city'] == 'Bogotá'
        assert result['supports_cold_chain'] is True
    
    def test_distribution_center_unique_code(self, db):
        dc1 = DistributionCenter(
            code='DC-UNIQUE',
            name='Center 1',
            city='City',
            country='Country'
        )
        db.session.add(dc1)
        db.session.commit()
        
        dc2 = DistributionCenter(
            code='DC-UNIQUE',
            name='Center 2',
            city='City',
            country='Country'
        )
        db.session.add(dc2)
        
        with pytest.raises(Exception):
            db.session.commit()
    
    def test_distribution_center_inventory_relationship(self, db, sample_distribution_center, sample_inventory):
        items = sample_distribution_center.inventory_items.all()
        assert len(items) == 1
        assert items[0].id == sample_inventory.id
