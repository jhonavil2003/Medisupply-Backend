import pytest
from decimal import Decimal
from src.commands.create_product import CreateProduct
from src.models.product import Product
from src.models.supplier import Supplier
from src.errors.errors import ValidationError, ApiError
from src.session import db


class TestCreateProduct:
    
    def test_create_product_success(self, app, sample_supplier):
        """Test successful product creation with all required fields"""
        with app.app_context():
            data = {
                'sku': 'TEST-CREATE-001',
                'name': 'Test Product Creation',
                'description': 'A test product for creation testing',
                'category': 'Test Category',
                'subcategory': 'Test Subcategory',
                'unit_price': 100.50,
                'currency': 'USD',
                'unit_of_measure': 'unidad',
                'supplier_id': sample_supplier.id,
                'requires_cold_chain': False,
                'manufacturer': 'Test Manufacturer',
                'country_of_origin': 'Test Country'
            }
            
            command = CreateProduct(data)
            result = command.execute()
            
            assert result['sku'] == 'TEST-CREATE-001'
            assert result['name'] == 'Test Product Creation'
            assert result['unit_price'] == 100.50
            assert result['supplier_id'] == sample_supplier.id
            assert result['is_active'] is True
            
            # Verify product was saved to database
            product = Product.query.filter_by(sku='TEST-CREATE-001').first()
            assert product is not None
            assert product.name == 'Test Product Creation'
    
    def test_create_product_minimal_required_fields(self, app, sample_supplier):
        """Test product creation with only required fields"""
        with app.app_context():
            data = {
                'sku': 'TEST-MIN-001',
                'name': 'Minimal Product',
                'category': 'Test',
                'unit_price': 50.00,
                'unit_of_measure': 'piece',
                'supplier_id': sample_supplier.id
            }
            
            command = CreateProduct(data)
            result = command.execute()
            
            assert result['sku'] == 'TEST-MIN-001'
            assert result['name'] == 'Minimal Product'
            assert result['currency'] == 'USD'  # default value
            assert result['requires_cold_chain'] is False  # default value
    
    def test_create_product_missing_required_field_sku(self, app):
        """Test validation error when SKU is missing"""
        with app.app_context():
            data = {
                'name': 'Product without SKU',
                'category': 'Test',
                'unit_price': 50.00,
                'unit_of_measure': 'piece',
                'supplier_id': 1
            }
            
            with pytest.raises(ValidationError) as exc_info:
                CreateProduct(data)
            
            assert "Field 'sku' is required" in exc_info.value.message
    
    def test_create_product_missing_required_field_name(self, app):
        """Test validation error when name is missing"""
        with app.app_context():
            data = {
                'sku': 'TEST-NO-NAME',
                'category': 'Test',
                'unit_price': 50.00,
                'unit_of_measure': 'piece',
                'supplier_id': 1
            }
            
            with pytest.raises(ValidationError) as exc_info:
                CreateProduct(data)
            
            assert "Field 'name' is required" in exc_info.value.message
    
    def test_create_product_missing_required_field_category(self, app):
        """Test validation error when category is missing"""
        with app.app_context():
            data = {
                'sku': 'TEST-NO-CAT',
                'name': 'Product without Category',
                'unit_price': 50.00,
                'unit_of_measure': 'piece',
                'supplier_id': 1
            }
            
            with pytest.raises(ValidationError) as exc_info:
                CreateProduct(data)
            
            assert "Field 'category' is required" in exc_info.value.message
    
    def test_create_product_missing_required_field_unit_price(self, app):
        """Test validation error when unit_price is missing"""
        with app.app_context():
            data = {
                'sku': 'TEST-NO-PRICE',
                'name': 'Product without Price',
                'category': 'Test',
                'unit_of_measure': 'piece',
                'supplier_id': 1
            }
            
            with pytest.raises(ValidationError) as exc_info:
                CreateProduct(data)
            
            assert "Field 'unit_price' is required" in exc_info.value.message
    
    def test_create_product_missing_required_field_unit_of_measure(self, app):
        """Test validation error when unit_of_measure is missing"""
        with app.app_context():
            data = {
                'sku': 'TEST-NO-UOM',
                'name': 'Product without UOM',
                'category': 'Test',
                'unit_price': 50.00,
                'supplier_id': 1
            }
            
            with pytest.raises(ValidationError) as exc_info:
                CreateProduct(data)
            
            assert "Field 'unit_of_measure' is required" in exc_info.value.message
    
    def test_create_product_missing_required_field_supplier_id(self, app):
        """Test validation error when supplier_id is missing"""
        with app.app_context():
            data = {
                'sku': 'TEST-NO-SUP',
                'name': 'Product without Supplier',
                'category': 'Test',
                'unit_price': 50.00,
                'unit_of_measure': 'piece'
            }
            
            with pytest.raises(ValidationError) as exc_info:
                CreateProduct(data)
            
            assert "Field 'supplier_id' is required" in exc_info.value.message
    
    def test_create_product_duplicate_sku(self, app, sample_product):
        """Test validation error when SKU already exists"""
        with app.app_context():
            data = {
                'sku': sample_product.sku,  # Use existing SKU
                'name': 'Duplicate SKU Product',
                'category': 'Test',
                'unit_price': 50.00,
                'unit_of_measure': 'piece',
                'supplier_id': sample_product.supplier_id
            }
            
            with pytest.raises(ValidationError) as exc_info:
                CreateProduct(data)
            
            assert f"Product with SKU '{sample_product.sku}' already exists" in exc_info.value.message
    
    def test_create_product_invalid_supplier_id(self, app):
        """Test validation error when supplier doesn't exist"""
        with app.app_context():
            data = {
                'sku': 'TEST-BAD-SUP',
                'name': 'Product with Invalid Supplier',
                'category': 'Test',
                'unit_price': 50.00,
                'unit_of_measure': 'piece',
                'supplier_id': 99999  # Non-existent supplier
            }
            
            with pytest.raises(ValidationError) as exc_info:
                CreateProduct(data)
            
            assert "Supplier with ID '99999' not found" in exc_info.value.message
    
    def test_create_product_negative_unit_price_validation(self, app, sample_supplier):
        """Test that negative unit price raises ValidationError"""
        with app.app_context():
            data = {
                'sku': 'TEST-NEG-PRICE',
                'name': 'Product with Negative Price',
                'category': 'Test',
                'unit_price': -10.00,
                'unit_of_measure': 'piece',
                'supplier_id': sample_supplier.id
            }
            
            # Should raise ValidationError for negative price
            with pytest.raises(ValidationError) as exc_info:
                CreateProduct(data)
            
            assert "greater than zero" in exc_info.value.message
    
    def test_create_product_zero_unit_price_validation(self, app, sample_supplier):
        """Test that zero unit price raises ValidationError"""
        with app.app_context():
            data = {
                'sku': 'TEST-ZERO-PRICE',
                'name': 'Product with Zero Price',
                'category': 'Test',
                'unit_price': 0.00,
                'unit_of_measure': 'piece',
                'supplier_id': sample_supplier.id
            }
            
            # Should raise ValidationError for zero price
            with pytest.raises(ValidationError) as exc_info:
                CreateProduct(data)
            
            assert "greater than zero" in exc_info.value.message
    
    def test_create_product_with_decimal_precision(self, app, sample_supplier):
        """Test product creation with decimal precision handling"""
        with app.app_context():
            data = {
                'sku': 'TEST-DECIMAL',
                'name': 'Product with Decimal Price',
                'category': 'Test',
                'unit_price': 123.456789,  # More precision than expected
                'unit_of_measure': 'piece',
                'supplier_id': sample_supplier.id
            }
            
            command = CreateProduct(data)
            result = command.execute()
            
            # Should be rounded to 2 decimal places
            assert result['unit_price'] == 123.46
    
    def test_create_product_with_physical_dimensions(self, app, sample_supplier):
        """Test product creation with physical dimensions"""
        with app.app_context():
            data = {
                'sku': 'TEST-DIMENSIONS',
                'name': 'Product with Dimensions',
                'category': 'Test',
                'unit_price': 75.00,
                'unit_of_measure': 'piece',
                'supplier_id': sample_supplier.id,
                'weight_kg': 2.5,
                'length_cm': 30.0,
                'width_cm': 20.0,
                'height_cm': 10.0
            }
            
            command = CreateProduct(data)
            result = command.execute()
            
            assert result['physical_dimensions']['weight_kg'] == 2.5
            assert result['physical_dimensions']['length_cm'] == 30.0
            assert result['physical_dimensions']['width_cm'] == 20.0
            assert result['physical_dimensions']['height_cm'] == 10.0
    
    def test_create_product_with_storage_conditions(self, app, sample_supplier):
        """Test product creation with storage conditions"""
        with app.app_context():
            data = {
                'sku': 'TEST-STORAGE',
                'name': 'Product with Storage Conditions',
                'category': 'Test',
                'unit_price': 85.00,
                'unit_of_measure': 'piece',
                'supplier_id': sample_supplier.id,
                'storage_temperature_min': 2.0,
                'storage_temperature_max': 8.0,
                'storage_humidity_max': 60.0
            }
            
            command = CreateProduct(data)
            result = command.execute()
            
            assert result['storage_conditions']['temperature_min'] == 2.0
            assert result['storage_conditions']['temperature_max'] == 8.0
            assert result['storage_conditions']['humidity_max'] == 60.0
    
    def test_create_product_with_regulatory_info(self, app, sample_supplier):
        """Test product creation with regulatory information"""
        with app.app_context():
            data = {
                'sku': 'TEST-REGULATORY',
                'name': 'Product with Regulatory Info',
                'category': 'Medical Device',
                'unit_price': 150.00,
                'unit_of_measure': 'piece',
                'supplier_id': sample_supplier.id,
                'requires_prescription': True,
                'regulatory_class': 'Class IIa',
                'sanitary_registration': 'REG-2024-001'
            }
            
            command = CreateProduct(data)
            result = command.execute()
            
            assert result['regulatory_info']['requires_prescription'] is True
            assert result['regulatory_info']['regulatory_class'] == 'Class IIa'
            assert result['regulatory_info']['sanitary_registration'] == 'REG-2024-001'

    def test_create_product_invalid_weight_kg(self, app, sample_supplier):
        """Test validation error for invalid weight_kg"""
        with app.app_context():
            data = {
                'sku': 'TEST-INVALID-WEIGHT',
                'name': 'Product with Invalid Weight',
                'category': 'Test',
                'unit_price': 10.00,
                'unit_of_measure': 'piece',
                'supplier_id': sample_supplier.id,
                'weight_kg': 'invalid_weight'  # Invalid weight
            }

            with pytest.raises(ValidationError) as exc_info:
                CreateProduct(data)
            
            assert "Invalid numeric values provided" in exc_info.value.message

    def test_create_product_database_error(self, app, sample_supplier, mocker):
        """Test that database errors during product creation are handled properly"""
        with app.app_context():
            data = {
                'sku': 'TEST-DB-ERROR',
                'name': 'Product DB Error Test',
                'category': 'Test',
                'unit_price': 10.00,
                'unit_of_measure': 'piece',
                'supplier_id': sample_supplier.id
            }

            # Mock db.session.commit to raise an exception
            mock_commit = mocker.patch('src.session.db.session.commit')
            mock_commit.side_effect = Exception("Database connection error")
            
            # Mock db.session.rollback to verify it's called
            mock_rollback = mocker.patch('src.session.db.session.rollback')
            
            command = CreateProduct(data)
            
            with pytest.raises(ApiError) as exc_info:
                command.execute()
            
            # Verify error message
            assert "Error creating product" in exc_info.value.message
            assert "Database connection error" in exc_info.value.message
            assert exc_info.value.status_code == 500
            
            # Verify rollback was called
            mock_rollback.assert_called_once()