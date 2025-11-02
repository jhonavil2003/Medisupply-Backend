import pytest
from src.commands.get_product_by_id import GetProductById
from src.errors.errors import NotFoundError


class TestGetProductById:
    
    def test_get_product_by_id_success(self, app, sample_product):
        """Test successful product retrieval by ID"""
        with app.app_context():
            command = GetProductById(product_id=sample_product.id)
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
    
    def test_get_product_by_id_not_found(self, app):
        """Test error when product ID doesn't exist"""
        with app.app_context():
            command = GetProductById(product_id=99999)
            
            with pytest.raises(NotFoundError) as exc_info:
                command.execute()
            
            assert "Product with ID '99999' not found" in exc_info.value.message
            assert exc_info.value.payload['product_id'] == 99999
    
    def test_get_product_by_id_invalid_id_none(self, app):
        """Test validation error when product_id is None"""
        with app.app_context():
            with pytest.raises(ValueError) as exc_info:
                GetProductById(product_id=None)
            
            assert 'Product ID is required' in str(exc_info.value)
    
    def test_get_product_by_id_invalid_id_zero(self, app):
        """Test validation error when product_id is zero"""
        with app.app_context():
            with pytest.raises(ValueError) as exc_info:
                GetProductById(product_id=0)
            
            assert 'Product ID must be a positive integer' in str(exc_info.value)
    
    def test_get_product_by_id_invalid_id_negative(self, app):
        """Test validation error when product_id is negative"""
        with app.app_context():
            with pytest.raises(ValueError) as exc_info:
                GetProductById(product_id=-1)
            
            assert 'Product ID must be a positive integer' in str(exc_info.value)
    
    def test_get_product_by_id_invalid_id_string(self, app):
        """Test validation error when product_id is not an integer"""
        with app.app_context():
            with pytest.raises(ValueError) as exc_info:
                GetProductById(product_id="invalid")
            
            assert 'Product ID must be a positive integer' in str(exc_info.value)
    
    def test_get_product_by_id_invalid_id_float(self, app):
        """Test validation error when product_id is a float"""
        with app.app_context():
            with pytest.raises(ValueError) as exc_info:
                GetProductById(product_id=1.5)
            
            assert 'Product ID must be a positive integer' in str(exc_info.value)
    
    def test_get_product_by_id_with_relationships(self, app, sample_product_with_relationships):
        """Test product retrieval includes all relationship data"""
        with app.app_context():
            command = GetProductById(product_id=sample_product_with_relationships.id)
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
    
    def test_get_product_by_id_inactive_product(self, app, sample_product):
        """Test that inactive products can still be retrieved by ID"""
        with app.app_context():
            # Store the product ID
            product_id = sample_product.id
            
            # Update the product directly in the database
            from src.session import db
            db.session.execute(
                db.text("UPDATE products SET is_active = :is_active WHERE id = :id"),
                {"is_active": False, "id": product_id}
            )
            db.session.commit()

            command = GetProductById(product_id=product_id)
            result = command.execute()

            assert result['id'] == product_id
            assert result['is_active'] is False

    def test_get_product_by_id_discontinued_product(self, app, sample_product):
        """Test that discontinued products can still be retrieved by ID"""
        with app.app_context():
            # Store the product ID
            product_id = sample_product.id
            
            # Update the product directly in the database
            from src.session import db
            db.session.execute(
                db.text("UPDATE products SET is_discontinued = :is_discontinued WHERE id = :id"),
                {"is_discontinued": True, "id": product_id}
            )
            db.session.commit()
            
            command = GetProductById(product_id=product_id)
            result = command.execute()
            
            assert result['id'] == product_id
            assert result['is_discontinued'] is True