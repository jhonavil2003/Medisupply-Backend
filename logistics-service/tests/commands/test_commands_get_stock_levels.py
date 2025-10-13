from src.commands.get_stock_levels import GetStockLevels


class TestGetStockLevelsCommand:
    
    def test_get_stock_single_product(self, db, multiple_inventory_items):
        command = GetStockLevels(product_sku='JER-001')
        result = command.execute()
        
        assert result['product_sku'] == 'JER-001'
        assert result['total_available'] == 150
        assert len(result['distribution_centers']) == 2
    
    def test_get_stock_multiple_products(self, db, multiple_inventory_items):
        command = GetStockLevels(product_skus=['JER-001', 'VAC-001'])
        result = command.execute()
        
        assert result['total_products'] == 2
        assert len(result['products']) == 2
    
    def test_get_stock_by_distribution_center(self, db, multiple_inventory_items, sample_distribution_center):
        command = GetStockLevels(
            product_sku='JER-001',
            distribution_center_id=sample_distribution_center.id
        )
        result = command.execute()
        
        assert len(result['distribution_centers']) == 1
        assert result['distribution_centers'][0]['quantity_available'] == 100
    
    def test_get_stock_only_available(self, db, multiple_inventory_items):
        command = GetStockLevels(product_skus=['JER-001', 'VAC-001', 'GUANTE-001'], only_available=True)
        result = command.execute()
        
        assert result['total_products'] == 2
    
    def test_get_stock_with_reserved(self, db, sample_inventory):
        command = GetStockLevels(product_sku='JER-001', include_reserved=True)
        result = command.execute()
        
        assert result['total_reserved'] == 10
        assert result['distribution_centers'][0]['quantity_reserved'] == 10
    
    def test_get_stock_with_in_transit(self, db, sample_inventory):
        command = GetStockLevels(product_sku='JER-001', include_in_transit=True)
        result = command.execute()
        
        assert result['total_in_transit'] == 5
        assert result['distribution_centers'][0]['quantity_in_transit'] == 5
    
    def test_get_stock_no_results(self, db, sample_distribution_center):
        command = GetStockLevels(product_sku='NONEXISTENT')
        result = command.execute()
        
        assert result['product_sku'] == 'NONEXISTENT'
        assert result['total_available'] == 0
        assert len(result['distribution_centers']) == 0
    
    def test_get_stock_case_insensitive(self, db, multiple_inventory_items):
        command = GetStockLevels(product_sku='jer-001')
        result = command.execute()
        
        assert result['product_sku'] == 'JER-001'
        assert result['total_available'] == 150
    
    def test_get_stock_includes_center_info(self, db, sample_inventory):
        command = GetStockLevels(product_sku='JER-001')
        result = command.execute()
        
        center = result['distribution_centers'][0]
        assert 'distribution_center_code' in center
        assert 'distribution_center_name' in center
        assert 'city' in center
        assert center['distribution_center_code'] == 'DC-001'
    
    def test_get_stock_low_stock_flag(self, db, sample_distribution_center):
        from src.models.inventory import Inventory
        
        inv = Inventory(
            product_sku='LOW-STOCK',
            distribution_center_id=sample_distribution_center.id,
            quantity_available=5,
            minimum_stock_level=20
        )
        db.session.add(inv)
        db.session.commit()
        
        command = GetStockLevels(product_sku='LOW-STOCK')
        result = command.execute()
        
        assert result['distribution_centers'][0]['is_low_stock'] is True
