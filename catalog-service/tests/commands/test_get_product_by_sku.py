import pytest
from src.commands.get_product_by_sku import GetProductBySKU
from src.errors.errors import NotFoundError


class TestGetProductBySKU:
    
    def test_get_product_by_sku_success(self, app, sample_product):
        """Test successful product retrieval by SKU"""
        with app.app_context():
            command = GetProductBySKU(sku=sample_product.sku)
            result = command.execute()
            
            assert result['id'] == sample_product.id
            assert result['sku'] == sample_product.sku
            assert result['name'] == sample_product.name
            assert result['category'] == sample_product.category
            assert float(result['unit_price']) == float(sample_product.unit_price)
            assert result['supplier_id'] == sample_product.supplier_id
            
            # Verify detailed information is included
            assert 'physical_dimensions' in result
            assert 'storage_conditions' in result
            assert 'regulatory_info' in result
            assert 'certifications' in result
            assert 'regulatory_conditions' in result
    
    def test_get_product_by_sku_lowercase_input(self, app, sample_product):
        """Test that SKU search is case-insensitive (converts to uppercase)"""
        with app.app_context():
            command = GetProductBySKU(sku=sample_product.sku.lower())
            result = command.execute()
            
            assert result['id'] == sample_product.id
            assert result['sku'] == sample_product.sku
    
    def test_get_product_by_sku_with_whitespace(self, app, sample_product):
        """Test that SKU is stripped of whitespace"""
        with app.app_context():
            command = GetProductBySKU(sku=f"  {sample_product.sku}  ")
            result = command.execute()
            
            assert result['id'] == sample_product.id
            assert result['sku'] == sample_product.sku
    
    def test_get_product_by_sku_not_found(self, app):
        """Test error when SKU doesn't exist"""
        with app.app_context():
            command = GetProductBySKU(sku='NONEXISTENT-SKU')
            
            with pytest.raises(NotFoundError) as exc_info:
                command.execute()
            
            assert "Product with SKU 'NONEXISTENT-SKU' not found" in exc_info.value.message
            assert exc_info.value.payload['sku'] == 'NONEXISTENT-SKU'
    
    def test_get_product_by_sku_empty_string(self, app):
        """Test validation error when SKU is empty string"""
        with app.app_context():
            with pytest.raises(ValueError) as exc_info:
                GetProductBySKU(sku='')
            
            assert 'SKU is required' in str(exc_info.value)
    
    def test_get_product_by_sku_none(self, app):
        """Test validation error when SKU is None"""
        with app.app_context():
            with pytest.raises(ValueError) as exc_info:
                GetProductBySKU(sku=None)
            
            assert 'SKU is required' in str(exc_info.value)
    
    def test_get_product_by_sku_whitespace_only(self, app):
        """Test validation error when SKU is only whitespace"""
        with app.app_context():
            with pytest.raises(ValueError) as exc_info:
                GetProductBySKU(sku='   ')
            
            assert 'SKU is required' in str(exc_info.value)
    
    def test_get_product_by_sku_with_relationships(self, app, sample_product_with_relationships):
        """Test product retrieval includes all relationship data"""
        with app.app_context():
            command = GetProductBySKU(sku=sample_product_with_relationships.sku)
            result = command.execute()
            
            # Should include supplier name
            assert 'supplier_name' in result
            
            # Should include physical dimensions if they exist
            if sample_product_with_relationships.weight_kg:
                assert result['physical_dimensions']['weight_kg'] == sample_product_with_relationships.weight_kg
            
            # Should include storage conditions if they exist
            if sample_product_with_relationships.storage_temperature_min:
                assert result['storage_conditions']['temperature_min'] == sample_product_with_relationships.storage_temperature_min
            
            # Should include regulatory info
            assert result['regulatory_info']['requires_prescription'] == sample_product_with_relationships.requires_prescription
    
    def test_get_product_by_sku_inactive_product(self, app, sample_product):
        """Test that inactive products can still be retrieved by SKU"""
        with app.app_context():
            # Store the SKU
            sku = sample_product.sku
            
            # Update the product directly in the database
            from src.session import db
            db.session.execute(
                db.text("UPDATE products SET is_active = :is_active WHERE sku = :sku"),
                {"is_active": False, "sku": sku}
            )
            db.session.commit()

            command = GetProductBySKU(sku=sku)
            result = command.execute()

            assert result['sku'] == sku
            assert result['is_active'] is False

    def test_get_product_by_sku_discontinued_product(self, app, sample_product):
        """Test that discontinued products can still be retrieved by SKU"""
        with app.app_context():
            # Store the SKU
            sku = sample_product.sku
            
            # Update the product directly in the database
            from src.session import db
            db.session.execute(
                db.text("UPDATE products SET is_discontinued = :is_discontinued WHERE sku = :sku"),
                {"is_discontinued": True, "sku": sku}
            )
            db.session.commit()
            
            command = GetProductBySKU(sku=sku)
            result = command.execute()
            
            assert result['sku'] == sku
            assert result['is_discontinued'] is True
