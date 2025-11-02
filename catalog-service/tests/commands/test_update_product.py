import pytest
from decimal import Decimal
from src.commands.update_product import UpdateProduct
from src.models.product import Product
from src.errors.errors import ValidationError, ApiError
from src.session import db


class TestUpdateProduct:
    
    def test_update_product_success_single_field(self, app, sample_product):
        """Test successful update of a single field"""
        with app.app_context():
            original_name = sample_product.name
            data = {'name': 'Updated Product Name'}
            
            command = UpdateProduct(product_id=sample_product.id, data=data)
            result = command.execute()
            
            assert result['name'] == 'Updated Product Name'
            assert result['id'] == sample_product.id
            # Other fields should remain unchanged
            assert result['sku'] == sample_product.sku
            assert result['category'] == sample_product.category
    
    def test_update_product_success_multiple_fields(self, app, sample_product):
        """Test successful update of multiple fields"""
        with app.app_context():
            data = {
                'name': 'Updated Name',
                'description': 'Updated description',
                'unit_price': 999.99,
                'requires_cold_chain': True
            }
            
            command = UpdateProduct(product_id=sample_product.id, data=data)
            result = command.execute()
            
            assert result['name'] == 'Updated Name'
            assert result['description'] == 'Updated description'
            assert result['unit_price'] == 999.99
            assert result['requires_cold_chain'] is True
            # Unchanged fields
            assert result['sku'] == sample_product.sku
            assert result['category'] == sample_product.category
    
    def test_update_product_success_price_with_decimal(self, app, sample_product):
        """Test updating price with decimal precision"""
        with app.app_context():
            data = {'unit_price': 123.456789}
            
            command = UpdateProduct(product_id=sample_product.id, data=data)
            result = command.execute()
            
            # Should be rounded to 2 decimal places
            assert result['unit_price'] == 123.46
    
    def test_update_product_success_physical_dimensions(self, app, sample_product):
        """Test updating physical dimensions"""
        with app.app_context():
            data = {
                'weight_kg': 2.5,
                'length_cm': 30.0,
                'width_cm': 20.0,
                'height_cm': 15.0
            }
            
            command = UpdateProduct(product_id=sample_product.id, data=data)
            result = command.execute()
            
            assert result['physical_dimensions']['weight_kg'] == 2.5
            assert result['physical_dimensions']['length_cm'] == 30.0
            assert result['physical_dimensions']['width_cm'] == 20.0
            assert result['physical_dimensions']['height_cm'] == 15.0
    
    def test_update_product_success_storage_conditions(self, app, sample_product):
        """Test updating storage conditions"""
        with app.app_context():
            data = {
                'storage_temperature_min': 2.0,
                'storage_temperature_max': 8.0,
                'storage_humidity_max': 70.0
            }
            
            command = UpdateProduct(product_id=sample_product.id, data=data)
            result = command.execute()
            
            assert result['storage_conditions']['temperature_min'] == 2.0
            assert result['storage_conditions']['temperature_max'] == 8.0
            assert result['storage_conditions']['humidity_max'] == 70.0
    
    def test_update_product_success_regulatory_info(self, app, sample_product):
        """Test updating regulatory information"""
        with app.app_context():
            data = {
                'requires_prescription': True,
                'regulatory_class': 'Class III',
                'sanitary_registration': 'REG-2024-UPD'
            }
            
            command = UpdateProduct(product_id=sample_product.id, data=data)
            result = command.execute()
            
            assert result['regulatory_info']['requires_prescription'] is True
            assert result['regulatory_info']['regulatory_class'] == 'Class III'
            assert result['regulatory_info']['sanitary_registration'] == 'REG-2024-UPD'
    
    def test_update_product_success_supplier_change(self, app, sample_product, sample_supplier):
        """Test updating supplier"""
        with app.app_context():
            # Create another supplier
            from src.models.supplier import Supplier
            new_supplier = Supplier(
                name='New Supplier',
                legal_name='New Supplier LLC',  # Required field
                tax_id='987654321',  # Required and must be unique
                email='new@supplier.com',
                phone='123456789',
                country='USA'  # Required field
            )
            db.session.add(new_supplier)
            db.session.commit()
            
            data = {'supplier_id': new_supplier.id}
            
            command = UpdateProduct(product_id=sample_product.id, data=data)
            result = command.execute()
            
            assert result['supplier_id'] == new_supplier.id
            assert result['supplier_name'] == 'New Supplier'
    
    def test_update_product_not_found(self, app):
        """Test error when product ID doesn't exist"""
        with app.app_context():
            data = {'name': 'Updated Name'}
            
            with pytest.raises(ApiError) as exc_info:
                UpdateProduct(product_id=99999, data=data)
            
            assert "Product with ID '99999' not found" in exc_info.value.message
            assert exc_info.value.status_code == 404
    
    def test_update_product_invalid_product_id_none(self, app):
        """Test validation error when product_id is None"""
        with app.app_context():
            data = {'name': 'Updated Name'}
            
            with pytest.raises(ValidationError) as exc_info:
                UpdateProduct(product_id=None, data=data)
            
            assert 'Product ID must be a positive integer' in exc_info.value.message
    
    def test_update_product_invalid_product_id_zero(self, app):
        """Test validation error when product_id is zero"""
        with app.app_context():
            data = {'name': 'Updated Name'}
            
            with pytest.raises(ValidationError) as exc_info:
                UpdateProduct(product_id=0, data=data)
            
            assert 'Product ID must be a positive integer' in exc_info.value.message
    
    def test_update_product_invalid_product_id_negative(self, app):
        """Test validation error when product_id is negative"""
        with app.app_context():
            data = {'name': 'Updated Name'}
            
            with pytest.raises(ValidationError) as exc_info:
                UpdateProduct(product_id=-1, data=data)
            
            assert 'Product ID must be a positive integer' in exc_info.value.message
    
    def test_update_product_invalid_product_id_string(self, app):
        """Test validation error when product_id is not an integer"""
        with app.app_context():
            data = {'name': 'Updated Name'}
            
            with pytest.raises(ValidationError) as exc_info:
                UpdateProduct(product_id="invalid", data=data)
            
            assert 'Product ID must be a positive integer' in exc_info.value.message
    
    def test_update_product_invalid_supplier_id(self, app, sample_product):
        """Test validation error when supplier doesn't exist"""
        with app.app_context():
            data = {'supplier_id': 99999}
            
            with pytest.raises(ValidationError) as exc_info:
                UpdateProduct(product_id=sample_product.id, data=data)
            
            assert "Supplier with ID '99999' not found" in exc_info.value.message
    
    def test_update_product_invalid_unit_price_negative(self, app, sample_product):
        """Test validation error for negative unit price"""
        with app.app_context():
            data = {'unit_price': -10.00}
            
            with pytest.raises(ValidationError) as exc_info:
                UpdateProduct(product_id=sample_product.id, data=data)
            
            assert 'greater than zero' in exc_info.value.message
    
    def test_update_product_invalid_unit_price_zero(self, app, sample_product):
        """Test validation error for zero unit price"""
        with app.app_context():
            data = {'unit_price': 0.00}
            
            with pytest.raises(ValidationError) as exc_info:
                UpdateProduct(product_id=sample_product.id, data=data)
            
            assert 'greater than zero' in exc_info.value.message
    
    def test_update_product_sku_unchanged(self, app, sample_product):
        """Test that SKU cannot be changed through update"""
        with app.app_context():
            original_sku = sample_product.sku
            data = {'sku': 'NEW-SKU'}
            
            command = UpdateProduct(product_id=sample_product.id, data=data)
            result = command.execute()
            
            # SKU should remain unchanged
            assert result['sku'] == original_sku
    
    def test_update_product_empty_data(self, app, sample_product):
        """Test update with empty data dictionary"""
        with app.app_context():
            data = {}
            
            command = UpdateProduct(product_id=sample_product.id, data=data)
            result = command.execute()
            
            # Should return the product unchanged
            assert result['id'] == sample_product.id
            assert result['name'] == sample_product.name
    
    def test_update_product_preserve_timestamps(self, app, sample_product):
        """Test that created_at is preserved and updated_at is changed"""
        with app.app_context():
            original_created_at = sample_product.created_at
            data = {'name': 'Updated Name'}
            
            command = UpdateProduct(product_id=sample_product.id, data=data)
            result = command.execute()
            
            # created_at should be unchanged
            assert result['created_at'] == original_created_at.isoformat()
            # updated_at should be different (more recent)
            assert result['updated_at'] != original_created_at.isoformat()
    
    def test_update_product_boolean_fields(self, app, sample_product):
        """Test updating boolean fields"""
        with app.app_context():
            data = {
                'requires_cold_chain': True,
                'requires_prescription': True,
                'is_discontinued': True
            }
            
            command = UpdateProduct(product_id=sample_product.id, data=data)
            result = command.execute()
            
            assert result['requires_cold_chain'] is True
            assert result['regulatory_info']['requires_prescription'] is True
            assert result['is_discontinued'] is True
    
    def test_update_product_string_fields_trimmed(self, app, sample_product):
        """Test that string fields are properly trimmed"""
        with app.app_context():
            data = {
                'name': '  Updated Name  ',
                'description': '  Updated description  ',
                'manufacturer': '  Updated Manufacturer  '
            }
            
            command = UpdateProduct(product_id=sample_product.id, data=data)
            result = command.execute()
            
            assert result['name'] == 'Updated Name'
            assert result['description'] == 'Updated description'
            assert result['manufacturer'] == 'Updated Manufacturer'

    def test_update_product_duplicate_sku_validation(self, app, sample_product, sample_supplier):
        """Test validation error when trying to change SKU to existing one"""
        with app.app_context():
            # Create another product with a different SKU
            from src.models.product import Product
            other_product = Product(
                sku='OTHER-SKU',
                name='Other Product',
                category='Test',
                unit_price=Decimal('50.00'),
                unit_of_measure='piece',
                supplier_id=sample_supplier.id,
                is_active=True,
                is_discontinued=False
            )
            db.session.add(other_product)
            db.session.commit()
            
            # Try to update sample_product to use the existing SKU
            data = {'sku': 'OTHER-SKU'}
            
            with pytest.raises(ValidationError) as exc_info:
                UpdateProduct(product_id=sample_product.id, data=data)
            
            assert "Product with SKU 'OTHER-SKU' already exists" in exc_info.value.message

    def test_update_product_invalid_numeric_field(self, app, sample_product):
        """Test validation error for invalid numeric field value"""
        with app.app_context():
            data = {'weight_kg': 'invalid_weight'}  # Invalid numeric value
            
            with pytest.raises(ValidationError) as exc_info:
                UpdateProduct(product_id=sample_product.id, data=data)
            
            assert "Invalid numeric value for field 'weight_kg'" in exc_info.value.message

    def test_update_product_database_error(self, app, sample_product, mocker):
        """Test that database errors during product update are handled properly"""
        with app.app_context():
            data = {'name': 'Updated Name'}
            
            # Mock db.session.commit to raise an exception
            mock_commit = mocker.patch('src.session.db.session.commit')
            mock_commit.side_effect = Exception("Database connection error")
            
            # Mock db.session.rollback to verify it's called
            mock_rollback = mocker.patch('src.session.db.session.rollback')
            
            command = UpdateProduct(product_id=sample_product.id, data=data)
            
            with pytest.raises(ApiError) as exc_info:
                command.execute()
            
            # Verify error message
            assert "Error updating product" in exc_info.value.message
            assert "Database connection error" in exc_info.value.message
            assert exc_info.value.status_code == 500
            
            # Verify rollback was called
            mock_rollback.assert_called_once()