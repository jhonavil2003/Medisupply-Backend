import pytest
from src.commands.get_product_by_sku import GetProductBySKU
from src.errors.errors import NotFoundError


class TestGetProductBySKUCommand:
    
    def test_get_product_by_sku_success(self, db, sample_product):
        command = GetProductBySKU(sku='TEST-001')
        result = command.execute()
        
        assert result is not None
        assert result['sku'] == 'TEST-001'
        assert result['name'] == 'Test Product'
    
    def test_get_product_by_sku_with_detailed_info(self, db, sample_product, sample_certification):
        command = GetProductBySKU(sku='TEST-001')
        result = command.execute()
        
        assert 'certifications' in result
        assert 'regulatory_conditions' in result
        assert len(result['certifications']) == 1
    
    def test_get_product_by_sku_case_sensitivity(self, db, sample_product):
        command_lower = GetProductBySKU(sku='test-001')
        command_mixed = GetProductBySKU(sku='TeSt-001')
        
        result_lower = command_lower.execute()
        result_mixed = command_mixed.execute()
        
        assert result_lower['sku'] == result_mixed['sku'] == 'TEST-001'
    
    def test_get_product_by_sku_with_whitespace(self, db, sample_product):
        command = GetProductBySKU(sku='  TEST-001  ')
        result = command.execute()
        
        assert result['sku'] == 'TEST-001'
    
    def test_get_product_by_sku_not_found(self, db):
        with pytest.raises(NotFoundError):
            command = GetProductBySKU(sku='NONEXISTENT')
            command.execute()
    
    def test_get_product_by_sku_not_found_with_payload(self, db):
        with pytest.raises(NotFoundError) as exc_info:
            command = GetProductBySKU(sku='MISSING-SKU')
            command.execute()
        
        error = exc_info.value
        assert 'MISSING-SKU' in error.message
    
    def test_get_product_empty_string(self, db):
        with pytest.raises(ValueError):
            GetProductBySKU(sku='')
    
    def test_get_product_whitespace_only(self, db):
        with pytest.raises(ValueError):
            GetProductBySKU(sku='   ')
    
    def test_get_product_inactive_product(self, db, sample_product):
        sample_product.is_active = False
        db.session.commit()
        
        command = GetProductBySKU(sku='TEST-001')
        result = command.execute()
        
        assert result['is_active'] is False
