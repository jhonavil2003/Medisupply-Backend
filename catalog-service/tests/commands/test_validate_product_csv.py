"""
Tests para el comando ValidateProductCSV
Cobertura de validación de estructura y contenido de CSV
"""
import pytest
import io
import csv
from decimal import Decimal
from src.commands.validate_product_csv import ValidateProductCSV, CSVValidationError
from src.models.supplier import Supplier
from src.models.product import Product


class TestValidateFileStructure:
    """Tests para validación de estructura del archivo CSV"""
    
    def test_validate_invalid_extension(self):
        """Debe rechazar archivos que no sean .csv"""
        validator = ValidateProductCSV()
        content = b"sku,name,category"
        
        is_valid, errors, total_rows = validator.validate_file_structure(content, "file.txt")
        
        assert is_valid is False
        assert "extensión .csv" in errors[0]
        assert total_rows == 0
    
    def test_validate_file_too_large(self):
        """Debe rechazar archivos que excedan el tamaño máximo"""
        validator = ValidateProductCSV()
        # Crear archivo de más de 20 MB
        large_content = b"x" * (21 * 1024 * 1024)
        
        is_valid, errors, total_rows = validator.validate_file_structure(large_content, "large.csv")
        
        assert is_valid is False
        assert "excede el tamaño máximo" in errors[0]
    
    def test_validate_latin1_encoding(self):
        """Debe manejar archivos con codificación Latin-1"""
        validator = ValidateProductCSV()
        content = 'sku,name,category,unit_price,currency,unit_of_measure,supplier_id\n'
        content += 'TEST-001,Ácido,Medicamentos,10.00,USD,unidad,1'
        
        is_valid, errors, total_rows = validator.validate_file_structure(content.encode('latin-1'), "test.csv")
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_missing_required_columns(self):
        """Debe rechazar CSV sin columnas requeridas"""
        validator = ValidateProductCSV()
        content = 'sku,name\nTEST-001,Test Product'
        
        is_valid, errors, total_rows = validator.validate_file_structure(content.encode('utf-8'), "test.csv")
        
        assert is_valid is False
        assert any("columnas requeridas" in e.lower() for e in errors)
    
    def test_validate_empty_file(self):
        """Debe rechazar archivos vacíos"""
        validator = ValidateProductCSV()
        content = ''
        
        is_valid, errors, total_rows = validator.validate_file_structure(content.encode('utf-8'), "empty.csv")
        
        assert is_valid is False
        assert total_rows == 0
    
    def test_validate_only_headers(self):
        """Debe rechazar archivos con solo headers"""
        validator = ValidateProductCSV()
        content = 'sku,name,category,unit_price,currency,unit_of_measure,supplier_id\n'
        
        is_valid, errors, total_rows = validator.validate_file_structure(content.encode('utf-8'), "headers.csv")
        
        assert is_valid is False
        assert "solo encabezados" in errors[0].lower() or "no contiene datos" in errors[0].lower()
    
    def test_validate_too_many_rows(self):
        """Debe rechazar archivos con más filas que el límite"""
        validator = ValidateProductCSV()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['sku', 'name', 'category', 'unit_price', 'currency', 'unit_of_measure', 'supplier_id'])
        
        # Generar más de MAX_ROWS filas
        for i in range(10001):
            writer.writerow([f'SKU-{i}', f'Product {i}', 'Medicamentos', '10.00', 'USD', 'unidad', '1'])
        
        is_valid, errors, total_rows = validator.validate_file_structure(
            output.getvalue().encode('utf-8'), "large.csv"
        )
        
        assert is_valid is False
        assert any("excede el máximo" in e for e in errors)
    
    def test_validate_valid_structure(self):
        """Debe aceptar archivos con estructura válida"""
        validator = ValidateProductCSV()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['sku', 'name', 'category', 'unit_price', 'currency', 'unit_of_measure', 'supplier_id'])
        writer.writerow(['TEST-001', 'Test Product', 'Medicamentos', '10.00', 'USD', 'unidad', '1'])
        writer.writerow(['TEST-002', 'Test Product 2', 'Equipos Médicos', '20.00', 'COP', 'caja', '2'])
        
        is_valid, errors, total_rows = validator.validate_file_structure(
            output.getvalue().encode('utf-8'), "valid.csv"
        )
        
        assert is_valid is True
        assert len(errors) == 0
        assert total_rows == 2
    
    def test_validate_with_optional_columns(self):
        """Debe aceptar CSV con columnas opcionales"""
        validator = ValidateProductCSV()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            'sku', 'name', 'category', 'unit_price', 'currency', 'unit_of_measure', 'supplier_id',
            'description', 'subcategory', 'storage_humidity_max', 'image_url', 'is_discontinued'
        ])
        writer.writerow([
            'TEST-001', 'Test', 'Medicamentos', '10.00', 'USD', 'unidad', '1',
            'Description', 'Sub', '60', 'http://example.com/img.jpg', 'false'
        ])
        
        is_valid, errors, total_rows = validator.validate_file_structure(
            output.getvalue().encode('utf-8'), "optional.csv"
        )
        
        assert is_valid is True
        assert total_rows == 1


class TestValidateRowData:
    """Tests para validación de datos de filas individuales"""
    
    def test_validate_row_missing_required_field(self):
        """Debe detectar campos requeridos faltantes"""
        validator = ValidateProductCSV()
        row = {
            'sku': '',  # Campo requerido vacío
            'name': 'Test Product',
            'category': 'Medicamentos',
            'unit_price': '10.00',
            'currency': 'USD',
            'unit_of_measure': 'unidad',
            'supplier_id': '1'
        }
        
        is_valid, error_msg = validator.validate_row_data(row, 1)
        
        assert is_valid is False
        assert 'sku' in error_msg.lower() and ('vacío' in error_msg.lower() or 'requerido' in error_msg.lower())
    
    def test_validate_row_invalid_category(self):
        """Debe detectar categorías inválidas"""
        validator = ValidateProductCSV()
        row = {
            'sku': 'TEST-001',
            'name': 'Test Product',
            'category': 'CategoríaInválida',
            'unit_price': '10.00',
            'currency': 'USD',
            'unit_of_measure': 'unidad',
            'supplier_id': '1'
        }
        
        is_valid, error_msg = validator.validate_row_data(row, 1)
        
        assert is_valid is False
        assert 'categoría' in error_msg.lower() and 'válida' in error_msg.lower()
    
    def test_validate_row_invalid_price_format(self):
        """Debe detectar precios con formato inválido"""
        validator = ValidateProductCSV()
        row = {
            'sku': 'TEST-001',
            'name': 'Test Product',
            'category': 'Medicamentos',
            'unit_price': 'abc',
            'currency': 'USD',
            'unit_of_measure': 'unidad',
            'supplier_id': '1'
        }
        
        is_valid, error_msg = validator.validate_row_data(row, 1)
        
        assert is_valid is False
        assert 'precio' in error_msg.lower() and 'inválido' in error_msg.lower()
    
    def test_validate_row_negative_price(self):
        """Debe detectar precios negativos"""
        validator = ValidateProductCSV()
        row = {
            'sku': 'TEST-001',
            'name': 'Test Product',
            'category': 'Medicamentos',
            'unit_price': '-10.00',
            'currency': 'USD',
            'unit_of_measure': 'unidad',
            'supplier_id': '1'
        }
        
        is_valid, error_msg = validator.validate_row_data(row, 1)
        
        assert is_valid is False
        assert 'precio' in error_msg.lower() and 'mayor' in error_msg.lower()
    
    def test_validate_row_invalid_currency(self):
        """Debe detectar monedas inválidas"""
        validator = ValidateProductCSV()
        row = {
            'sku': 'TEST-001',
            'name': 'Test Product',
            'category': 'Medicamentos',
            'unit_price': '10.00',
            'currency': 'GBP',
            'unit_of_measure': 'unidad',
            'supplier_id': '1'
        }
        
        is_valid, error_msg = validator.validate_row_data(row, 1)
        
        assert is_valid is False
        assert 'moneda' in error_msg.lower() and 'válida' in error_msg.lower()
    
    def test_validate_row_invalid_supplier_id_format(self):
        """Debe detectar supplier_id no numérico"""
        validator = ValidateProductCSV()
        row = {
            'sku': 'TEST-001',
            'name': 'Test Product',
            'category': 'Medicamentos',
            'unit_price': '10.00',
            'currency': 'USD',
            'unit_of_measure': 'unidad',
            'supplier_id': 'abc'
        }
        
        is_valid, error_msg = validator.validate_row_data(row, 1)
        
        assert is_valid is False
        assert 'supplier' in error_msg.lower() and 'numérico' in error_msg.lower()
    
    def test_validate_row_invalid_boolean(self):
        """Debe detectar valores booleanos inválidos"""
        validator = ValidateProductCSV()
        row = {
            'sku': 'TEST-001',
            'name': 'Test Product',
            'category': 'Medicamentos',
            'unit_price': '10.00',
            'currency': 'USD',
            'unit_of_measure': 'unidad',
            'supplier_id': '1',
            'requires_cold_chain': 'maybe'
        }
        
        is_valid, error_msg = validator.validate_row_data(row, 1)
        
        assert is_valid is False
        assert 'booleano' in error_msg.lower() or 'true' in error_msg.lower() or 'false' in error_msg.lower()
    
    def test_validate_row_valid_data(self):
        """Debe aceptar filas con datos válidos"""
        validator = ValidateProductCSV()
        row = {
            'sku': 'TEST-001',
            'name': 'Test Product',
            'category': 'Medicamentos',
            'unit_price': '10.50',
            'currency': 'USD',
            'unit_of_measure': 'unidad',
            'supplier_id': '1'
        }
        
        is_valid, error_msg = validator.validate_row_data(row, 1)
        
        assert is_valid is True
        assert error_msg is None
    
    def test_validate_row_with_optional_fields(self):
        """Debe aceptar filas con campos opcionales válidos"""
        validator = ValidateProductCSV()
        row = {
            'sku': 'TEST-001',
            'name': 'Test Product',
            'category': 'Medicamentos',
            'unit_price': '10.50',
            'currency': 'USD',
            'unit_of_measure': 'unidad',
            'supplier_id': '1',
            'description': 'Product description',
            'requires_cold_chain': 'true',
            'storage_temperature_min': '2',
            'storage_temperature_max': '8',
            'storage_humidity_max': '60',
            'is_discontinued': 'false'
        }
        
        is_valid, error_msg = validator.validate_row_data(row, 1)
        
        assert is_valid is True
        assert error_msg is None


class TestValidateBusinessRules:
    """Tests para validación de reglas de negocio"""
    
    def test_validate_business_duplicate_sku_in_database(self, app):
        """Debe detectar SKUs que ya existen en la base de datos"""
        with app.app_context():
            from src.session import db
            
            # Crear proveedor
            supplier = Supplier(
                name='Test Supplier',
                legal_name='Test Supplier LLC',
                tax_id='123456789',
                country='Colombia'
            )
            db.session.add(supplier)
            db.session.commit()
            
            # Crear producto existente
            existing_product = Product(
                sku='EXISTING-SKU',
                name='Existing Product',
                category='Medicamentos',
                unit_price=10.00,
                currency='USD',
                unit_of_measure='unidad',
                supplier_id=supplier.id
            )
            db.session.add(existing_product)
            db.session.commit()
            
            validator = ValidateProductCSV()
            row = {
                'sku': 'EXISTING-SKU',
                'name': 'Test Product',
                'category': 'Medicamentos',
                'unit_price': '10.00',
                'currency': 'USD',
                'unit_of_measure': 'unidad',
                'supplier_id': str(supplier.id)
            }
            
            is_valid, error_msg = validator.validate_business_rules(row, 1)
            
            assert is_valid is False
            assert 'ya existe' in error_msg.lower()
    
    def test_validate_business_invalid_supplier(self, app):
        """Debe detectar supplier_id que no existe"""
        with app.app_context():
            validator = ValidateProductCSV()
            row = {
                'sku': 'TEST-001',
                'name': 'Test Product',
                'category': 'Medicamentos',
                'unit_price': '10.00',
                'currency': 'USD',
                'unit_of_measure': 'unidad',
                'supplier_id': '99999'
            }
            
            is_valid, error_msg = validator.validate_business_rules(row, 1)
            
            assert is_valid is False
            assert 'no existe' in error_msg.lower()
    
    def test_validate_business_inactive_supplier(self, app):
        """Debe detectar proveedores inactivos"""
        with app.app_context():
            from src.session import db
            
            # Crear proveedor inactivo
            supplier = Supplier(
                name='Inactive Supplier',
                legal_name='Inactive Supplier LLC',
                tax_id='987654321',
                country='Colombia',
                is_active=False
            )
            db.session.add(supplier)
            db.session.commit()
            
            validator = ValidateProductCSV()
            row = {
                'sku': 'TEST-001',
                'name': 'Test Product',
                'category': 'Medicamentos',
                'unit_price': '10.00',
                'currency': 'USD',
                'unit_of_measure': 'unidad',
                'supplier_id': str(supplier.id)
            }
            
            is_valid, error_msg = validator.validate_business_rules(row, 1)
            
            assert is_valid is False
            assert 'inactivo' in error_msg.lower()
    
    def test_validate_business_valid_supplier(self, app):
        """Debe aceptar proveedores válidos y activos"""
        with app.app_context():
            from src.session import db
            
            # Crear proveedor activo
            supplier = Supplier(
                name='Active Supplier',
                legal_name='Active Supplier LLC',
                tax_id='111222333',
                country='Colombia',
                is_active=True
            )
            db.session.add(supplier)
            db.session.commit()
            
            validator = ValidateProductCSV()
            row = {
                'sku': 'NEW-SKU-001',
                'name': 'Test Product',
                'category': 'Medicamentos',
                'unit_price': '10.00',
                'currency': 'USD',
                'unit_of_measure': 'unidad',
                'supplier_id': str(supplier.id)
            }
            
            is_valid, error_msg = validator.validate_business_rules(row, 1)
            
            assert is_valid is True
            assert error_msg is None


class TestParseCSVToList:
    """Tests para parseo de CSV a lista"""
    
    def test_parse_csv_simple(self):
        """Debe parsear CSV simple correctamente"""
        validator = ValidateProductCSV()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['sku', 'name', 'category', 'unit_price', 'currency', 'unit_of_measure', 'supplier_id'])
        writer.writerow(['TEST-001', 'Product 1', 'Medicamentos', '10.00', 'USD', 'unidad', '1'])
        writer.writerow(['TEST-002', 'Product 2', 'Equipos Médicos', '20.00', 'COP', 'caja', '2'])
        
        rows = validator.parse_csv_to_list(output.getvalue().encode('utf-8'))
        
        assert len(rows) == 2
        assert rows[0]['sku'] == 'TEST-001'
        assert rows[1]['sku'] == 'TEST-002'


