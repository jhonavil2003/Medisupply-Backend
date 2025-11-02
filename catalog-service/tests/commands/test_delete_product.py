import pytest
from src.commands.delete_product import DeleteProduct
from src.models.product import Product
from src.errors.errors import ValidationError, ApiError
from src.session import db


class TestDeleteProduct:
    
    def test_delete_product_soft_delete_success(self, app, sample_product):
        """Test successful soft delete (default behavior)"""
        with app.app_context():
            original_sku = sample_product.sku
            assert sample_product.is_active is True
            assert sample_product.is_discontinued is False
            
            command = DeleteProduct(product_id=sample_product.id)
            result = command.execute()
            
            # Check response
            assert f"Product '{original_sku}' has been deactivated successfully" in result['message']
            assert result['deleted_product']['id'] == sample_product.id
            assert result['deleted_product']['sku'] == original_sku
            
            # Verify product is soft deleted in database
            product = Product.query.filter_by(id=sample_product.id).first()
            assert product is not None  # Still exists in database
            assert product.is_active is False
            assert product.is_discontinued is True
    
    def test_delete_product_hard_delete_success(self, app, sample_product):
        """Test successful hard delete"""
        with app.app_context():
            product_id = sample_product.id
            original_sku = sample_product.sku
            
            command = DeleteProduct(product_id=sample_product.id)
            result = command.execute_hard_delete()
            
            # Check response
            assert f"Product '{original_sku}' has been permanently deleted" in result['message']
            assert result['deleted_product']['id'] == product_id
            assert result['deleted_product']['sku'] == original_sku
            
            # Verify product is completely removed from database
            product = Product.query.filter_by(id=product_id).first()
            assert product is None
    
    def test_delete_product_not_found(self, app):
        """Test error when product ID doesn't exist"""
        with app.app_context():
            with pytest.raises(ApiError) as exc_info:
                DeleteProduct(product_id=99999)
            
            assert "Product with ID '99999' not found" in exc_info.value.message
            assert exc_info.value.status_code == 404
    
    def test_delete_product_invalid_product_id_none(self, app):
        """Test validation error when product_id is None"""
        with app.app_context():
            with pytest.raises(ValidationError) as exc_info:
                DeleteProduct(product_id=None)
            
            assert 'Product ID must be a positive integer' in exc_info.value.message
    
    def test_delete_product_invalid_product_id_zero(self, app):
        """Test validation error when product_id is zero"""
        with app.app_context():
            with pytest.raises(ValidationError) as exc_info:
                DeleteProduct(product_id=0)
            
            assert 'Product ID must be a positive integer' in exc_info.value.message
    
    def test_delete_product_invalid_product_id_negative(self, app):
        """Test validation error when product_id is negative"""
        with app.app_context():
            with pytest.raises(ValidationError) as exc_info:
                DeleteProduct(product_id=-1)
            
            assert 'Product ID must be a positive integer' in exc_info.value.message
    
    def test_delete_product_invalid_product_id_string(self, app):
        """Test validation error when product_id is not an integer"""
        with app.app_context():
            with pytest.raises(ValidationError) as exc_info:
                DeleteProduct(product_id="invalid")
            
            assert 'Product ID must be a positive integer' in exc_info.value.message
    
    def test_delete_product_invalid_product_id_float(self, app):
        """Test validation error when product_id is a float"""
        with app.app_context():
            with pytest.raises(ValidationError) as exc_info:
                DeleteProduct(product_id=1.5)
            
            assert 'Product ID must be a positive integer' in exc_info.value.message
    
    def test_delete_product_already_inactive(self, app, sample_product):
        """Test soft delete on already inactive product"""
        with app.app_context():
            # Store the product ID  
            product_id = sample_product.id
            
            # Update the product directly in the database to deactivate it
            from src.session import db
            db.session.execute(
                db.text("UPDATE products SET is_active = :is_active WHERE id = :id"),
                {"is_active": False, "id": product_id}
            )
            db.session.commit()

            command = DeleteProduct(product_id=product_id)
            result = command.execute()

            # Should still work and return success message
            assert 'has been deactivated successfully' in result['message']
            # The returned product data should show the state when the product was originally created
            # (the delete command captures the product data before performing the delete operation)
            assert result['deleted_product']['is_active'] is False  # Product was already inactive

    def test_delete_product_already_discontinued(self, app, sample_product):
        """Test soft delete on already discontinued product"""
        with app.app_context():
            # Pre-discontinue the product
            sample_product.is_discontinued = True
            db.session.commit()
            
            command = DeleteProduct(product_id=sample_product.id)
            result = command.execute()
            
            # Should still work and set is_active to False
            assert 'has been deactivated successfully' in result['message']
            # Should set both flags
            
            # Verify final state
            product = Product.query.filter_by(id=sample_product.id).first()
            assert product.is_active is False
            assert product.is_discontinued is True
    
    def test_delete_product_soft_preserves_data(self, app, sample_product):
        """Test that soft delete preserves all product data"""
        with app.app_context():
            # Store original data
            original_data = {
                'name': sample_product.name,
                'sku': sample_product.sku,
                'description': sample_product.description,
                'category': sample_product.category,
                'unit_price': sample_product.unit_price,
                'supplier_id': sample_product.supplier_id
            }
            
            command = DeleteProduct(product_id=sample_product.id)
            result = command.execute()
            
            # Verify all data is preserved in response
            deleted_product = result['deleted_product']
            assert deleted_product['name'] == original_data['name']
            assert deleted_product['sku'] == original_data['sku']
            assert deleted_product['description'] == original_data['description']
            assert deleted_product['category'] == original_data['category']
            assert float(deleted_product['unit_price']) == float(original_data['unit_price'])
            assert deleted_product['supplier_id'] == original_data['supplier_id']
            
            # Verify data is preserved in database
            product = Product.query.filter_by(id=sample_product.id).first()
            assert product.name == original_data['name']
            assert product.sku == original_data['sku']
            assert product.description == original_data['description']
    
    def test_delete_product_hard_removes_completely(self, app, sample_product):
        """Test that hard delete removes product completely"""
        with app.app_context():
            product_id = sample_product.id
            
            command = DeleteProduct(product_id=sample_product.id)
            result = command.execute_hard_delete()
            
            # Verify product is completely gone
            product = Product.query.filter_by(id=product_id).first()
            assert product is None
            
            # Also verify by SKU
            product_by_sku = Product.query.filter_by(sku=result['deleted_product']['sku']).first()
            assert product_by_sku is None
    
    def test_delete_product_updates_timestamp_soft(self, app, sample_product):
        """Test that soft delete updates the updated_at timestamp"""
        with app.app_context():
            original_updated_at = sample_product.updated_at
            
            command = DeleteProduct(product_id=sample_product.id)
            result = command.execute()
            
            # Verify timestamp was updated
            product = Product.query.filter_by(id=sample_product.id).first()
            assert product.updated_at > original_updated_at
    
    def test_delete_product_soft_delete_idempotent(self, app, sample_product):
        """Test that multiple soft deletes are idempotent"""
        with app.app_context():
            # First delete
            command1 = DeleteProduct(product_id=sample_product.id)
            result1 = command1.execute()
            
            # Second delete on same product
            command2 = DeleteProduct(product_id=sample_product.id)
            result2 = command2.execute()
            
            # Both should succeed
            assert 'deactivated successfully' in result1['message']
            assert 'deactivated successfully' in result2['message']
            
            # Final state should be the same
            product = Product.query.filter_by(id=sample_product.id).first()
            assert product.is_active is False
            assert product.is_discontinued is True
    
    def test_delete_product_with_relationships_soft(self, app, sample_product_with_relationships):
        """Test soft delete preserves relationships"""
        with app.app_context():
            command = DeleteProduct(product_id=sample_product_with_relationships.id)
            result = command.execute()
            
            # Product should still exist with relationships intact
            product = Product.query.filter_by(id=sample_product_with_relationships.id).first()
            assert product is not None
            assert product.is_active is False
            
            # Relationships should be preserved
            assert product.supplier_id == sample_product_with_relationships.supplier_id
    
    def test_delete_product_with_relationships_hard(self, app, sample_product_with_relationships):
        """Test hard delete removes product but preserves referenced entities"""
        with app.app_context():
            supplier_id = sample_product_with_relationships.supplier_id
            product_id = sample_product_with_relationships.id
            
            command = DeleteProduct(product_id=sample_product_with_relationships.id)
            result = command.execute_hard_delete()
            
            # Product should be completely gone
            product = Product.query.filter_by(id=product_id).first()
            assert product is None
            
            # But supplier should still exist
            from src.models.supplier import Supplier
            supplier = Supplier.query.filter_by(id=supplier_id).first()
            assert supplier is not None

    def test_delete_product_execute_database_error(self, app, sample_product, mocker):
        """Test that database errors in execute() are handled properly"""
        with app.app_context():
            # Mock db.session.commit to raise an exception
            mock_commit = mocker.patch('src.session.db.session.commit')
            mock_commit.side_effect = Exception("Database connection error")
            
            # Mock db.session.rollback to verify it's called
            mock_rollback = mocker.patch('src.session.db.session.rollback')
            
            command = DeleteProduct(product_id=sample_product.id)
            
            with pytest.raises(ApiError) as exc_info:
                command.execute()
            
            # Verify error message
            assert "Error deleting product" in exc_info.value.message
            assert "Database connection error" in exc_info.value.message
            assert exc_info.value.status_code == 500
            
            # Verify rollback was called
            mock_rollback.assert_called_once()

    def test_delete_product_execute_hard_delete_database_error(self, app, sample_product, mocker):
        """Test that database errors in execute_hard_delete() are handled properly"""
        with app.app_context():
            # Mock db.session.commit to raise an exception
            mock_commit = mocker.patch('src.session.db.session.commit')
            mock_commit.side_effect = Exception("Database connection error")
            
            # Mock db.session.rollback to verify it's called
            mock_rollback = mocker.patch('src.session.db.session.rollback')
            
            command = DeleteProduct(product_id=sample_product.id)
            
            with pytest.raises(ApiError) as exc_info:
                command.execute_hard_delete()
            
            # Verify error message
            assert "Error permanently deleting product" in exc_info.value.message
            assert "Database connection error" in exc_info.value.message
            assert exc_info.value.status_code == 500
            
            # Verify rollback was called
            mock_rollback.assert_called_once()