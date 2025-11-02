from src.commands.get_products import GetProducts


class TestGetProductsCommand:
    
    def test_get_products_default_params(self, db, multiple_products):
        command = GetProducts()
        result = command.execute()
        
        assert 'products' in result
        assert 'pagination' in result
        assert len(result['products']) == 3
    
    def test_get_products_pagination(self, db, multiple_products):
        command = GetProducts(page=1, per_page=2)
        result = command.execute()
        
        pagination = result['pagination']
        assert pagination['page'] == 1
        assert pagination['per_page'] == 2
        assert len(result['products']) == 2
        assert pagination['total_items'] == 3
        assert pagination['has_next'] is True
        assert pagination['has_prev'] is False
    
    def test_get_products_page_2(self, db, multiple_products):
        command = GetProducts(page=2, per_page=2)
        result = command.execute()
        
        pagination = result['pagination']
        assert pagination['page'] == 2
        assert len(result['products']) == 1
        assert pagination['has_next'] is False
    
    def test_get_products_search_by_name(self, db, multiple_products):
        command = GetProducts(search='jeringa')
        result = command.execute()
        
        assert len(result['products']) == 1
        assert result['products'][0]['sku'] == 'JER-001'
    
    def test_get_products_filter_by_category(self, db, multiple_products):
        command = GetProducts(category='Instrumental')
        result = command.execute()
        
        assert len(result['products']) == 1
        assert result['products'][0]['category'] == 'Instrumental'
    
    def test_get_products_filter_by_subcategory(self, db, multiple_products):
        command = GetProducts(subcategory='Vacunas')
        result = command.execute()
        
        assert len(result['products']) == 1
        assert result['products'][0]['sku'] == 'VAC-001'
    
    def test_get_products_filter_by_supplier(self, db, multiple_products, sample_supplier):
        command = GetProducts(supplier_id=sample_supplier.id)
        result = command.execute()
        
        assert len(result['products']) == 3
    
    def test_get_products_filter_cold_chain_true(self, db, multiple_products):
        command = GetProducts(requires_cold_chain=True)
        result = command.execute()
        
        assert len(result['products']) == 1
        assert result['products'][0]['requires_cold_chain'] is True
    
    def test_get_products_filter_is_active_false(self, db, multiple_products):
        command = GetProducts(is_active=False)
        result = command.execute()
        
        assert len(result['products']) == 1
        assert result['products'][0]['sku'] == 'INACTIVE-001'
    
    def test_get_products_combined_filters(self, db, multiple_products):
        command = GetProducts(
            category='Medicamentos',
            requires_cold_chain=True
        )
        result = command.execute()
        
        assert len(result['products']) == 1
        assert result['products'][0]['sku'] == 'VAC-001'
    
    def test_get_products_no_results(self, db, multiple_products):
        command = GetProducts(search='nonexistent product')
        result = command.execute()
        
        assert len(result['products']) == 0
        assert result['pagination']['total_items'] == 0

    def test_get_products_filter_by_sku(self, db, multiple_products):
        """Test filtering products by SKU"""
        command = GetProducts(sku='JER')  # Should match JER-001
        result = command.execute()
        
        assert len(result['products']) == 1
        assert result['products'][0]['sku'] == 'JER-001'
        assert 'JER' in result['products'][0]['sku']
