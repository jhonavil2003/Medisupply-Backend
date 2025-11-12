"""
Tests para ValidateProductCSV command.
Cubre validación de estructura, datos y reglas de negocio.
"""
import pytest
import io
from src.commands.validate_supplier_csv import ValidateProductCSV
from src.models.supplier import Supplier


class TestValidateFileStructure:
    """Tests para el método validate_file_structure"""
    
    def test_validate_valid_csv(self):
        """Verifica que acepta un CSV válido con todas las columnas requeridas"""
        validator = ValidateProductCSV()
        
        csv_content = b"sku,name,address_line1,phone,email,country\n123456789,Test Supplier,123 Main St,555-1234,test@example.com,Colombia\n"
        
        is_valid, errors, total_rows = validator.validate_file_structure(csv_content, 'test.csv')
        
        assert is_valid is True
        assert len(errors) == 0
        assert total_rows == 1
    
    def test_validate_invalid_extension(self):
        """Verifica que rechaza archivos que no son CSV"""
        validator = ValidateProductCSV()
        
        content = b"some content"
        
        is_valid, errors, total_rows = validator.validate_file_structure(content, 'test.txt')
        
        assert is_valid is False
        assert 'extensión .csv' in errors[0]
        assert total_rows == 0
    
    def test_validate_file_too_large(self):
        """Verifica que rechaza archivos demasiado grandes"""
        validator = ValidateProductCSV()
        
        # Crear contenido > 20MB
        large_content = b"x" * (21 * 1024 * 1024)
        
        is_valid, errors, total_rows = validator.validate_file_structure(large_content, 'large.csv')
        
        assert is_valid is False
        assert 'tamaño máximo' in errors[0]
    
    def test_validate_missing_required_columns(self):
        """Verifica que detecta columnas requeridas faltantes"""
        validator = ValidateProductCSV()
        
        # CSV sin columna 'email'
        csv_content = b"sku,name,address_line1,phone,country\n123456789,Test,123 Main St,555-1234,Colombia\n"
        
        is_valid, errors, total_rows = validator.validate_file_structure(csv_content, 'test.csv')
        
        assert is_valid is False
        assert any('email' in error for error in errors)
    
    def test_validate_empty_csv(self):
        """Verifica que rechaza CSV sin datos"""
        validator = ValidateProductCSV()
        
        csv_content = b"sku,name,address_line1,phone,email,country\n"
        
        is_valid, errors, total_rows = validator.validate_file_structure(csv_content, 'empty.csv')
        
        assert is_valid is False
        assert 'no contiene datos' in errors[0]
    
    def test_validate_too_many_rows(self):
        """Verifica que rechaza archivos con demasiadas filas"""
        validator = ValidateProductCSV()
        
        # Crear CSV con > 10000 filas
        header = "sku,name,address_line1,phone,email,country\n"
        rows = ""
        for i in range(10001):
            rows += f"TAX{i},Supplier{i},Address{i},555-{i},email{i}@test.com,Colombia\n"
        
        csv_content = (header + rows).encode('utf-8')
        
        is_valid, errors, total_rows = validator.validate_file_structure(csv_content, 'huge.csv')
        
        assert is_valid is False
        assert 'máximo de' in errors[0]
    
    def test_validate_unknown_columns_warning(self):
        """Verifica que genera advertencia para columnas desconocidas"""
        validator = ValidateProductCSV()
        
        csv_content = b"sku,name,address_line1,phone,email,country,unknown_column\n123456789,Test,123 Main,555-1234,test@test.com,Colombia,value\n"
        
        is_valid, errors, total_rows = validator.validate_file_structure(csv_content, 'test.csv')
        
        assert is_valid is True
        assert len(validator.warnings) > 0
        assert 'unknown_column' in validator.warnings[0]
    
    def test_validate_latin1_encoding(self):
        """Verifica que maneja archivos con encoding Latin-1"""
        validator = ValidateProductCSV()
        
        # Contenido con caracteres Latin-1 (ñ, á, etc)
        csv_content = "sku,name,address_line1,phone,email,country\n123456789,Peña González,Calle José María 123,555-1234,test@test.com,Colombia\n".encode('latin-1')
        
        is_valid, errors, total_rows = validator.validate_file_structure(csv_content, 'test.csv')
        
        assert is_valid is True
        assert total_rows == 1
    
    def test_validate_csv_parse_error(self):
        """Verifica que maneja errores de parseo de CSV"""
        validator = ValidateProductCSV()
        
        # CSV malformado con comillas sin cerrar
        csv_content = b'sku,name,address_line1,phone,email,country\n"123456789,"Test",123 Main,555-1234,test@test.com,Colombia\n'
        
        is_valid, errors, total_rows = validator.validate_file_structure(csv_content, 'test.csv')
        
        # Puede ser válido o inválido dependiendo del parser, pero no debe crashear
        assert isinstance(is_valid, bool)
    
    def test_validate_empty_file(self):
        """Verifica que rechaza archivos completamente vacíos"""
        validator = ValidateProductCSV()
        
        csv_content = b""
        
        is_valid, errors, total_rows = validator.validate_file_structure(csv_content, 'test.csv')
        
        assert is_valid is False
        assert any('vacío' in error.lower() for error in errors)
    
    def test_validate_only_whitespace(self):
        """Verifica que rechaza archivos con solo espacios en blanco"""
        validator = ValidateProductCSV()
        
        csv_content = b"   \n\n   \n"
        
        is_valid, errors, total_rows = validator.validate_file_structure(csv_content, 'test.csv')
        
        assert is_valid is False
    
    def test_validate_csv_with_utf8_bom(self):
        """Verifica que maneja correctamente UTF-8 con BOM"""
        validator = ValidateProductCSV()
        
        # CSV con BOM
        csv_content = b"\xef\xbb\xbfsku,name,address_line1,phone,email,country\n123456789,Test,123 Main,555-1234,test@test.com,Colombia\n"
        
        is_valid, errors, total_rows = validator.validate_file_structure(csv_content, 'test.csv')
        
        assert is_valid is True
        assert total_rows == 1


class TestValidateRowData:
    """Tests para el método validate_row_data"""
    
    def test_validate_valid_row(self):
        """Verifica que acepta una fila con todos los campos válidos"""
        validator = ValidateProductCSV()
        
        row = {
            'sku': '123456789',
            'name': 'Test Supplier Inc',
            'address_line1': '123 Main Street',
            'phone': '555-1234',
            'email': 'contact@testsupplier.com',
            'country': 'Colombia'
        }
        
        is_valid, error = validator.validate_row_data(row, 2)
        
        assert is_valid is True
        assert error is None
    
    def test_validate_missing_required_field(self):
        """Verifica que detecta campos requeridos vacíos"""
        validator = ValidateProductCSV()
        
        row = {
            'sku': '123456789',
            'name': '',  # Campo vacío
            'address_line1': '123 Main St',
            'phone': '555-1234',
            'email': 'test@test.com',
            'country': 'Colombia'
        }
        
        is_valid, error = validator.validate_row_data(row, 2)
        
        assert is_valid is False
        assert 'name' in error
        assert 'vacío' in error
    
    def test_validate_sku_too_short(self):
        """Verifica que rechaza sku muy corto"""
        validator = ValidateProductCSV()
        
        row = {
            'sku': '123',  # Muy corto
            'name': 'Test Supplier',
            'address_line1': '123 Main St',
            'phone': '555-1234',
            'email': 'test@test.com',
            'country': 'Colombia'
        }
        
        is_valid, error = validator.validate_row_data(row, 2)
        
        assert is_valid is False
        assert 'sku' in error.lower() or 'ruc' in error.lower()
    
    def test_validate_name_too_short(self):
        """Verifica que rechaza nombres muy cortos"""
        validator = ValidateProductCSV()
        
        row = {
            'sku': '123456789',
            'name': 'AB',  # Muy corto
            'address_line1': '123 Main St',
            'phone': '555-1234',
            'email': 'test@test.com',
            'country': 'Colombia'
        }
        
        is_valid, error = validator.validate_row_data(row, 2)
        
        assert is_valid is False
        assert 'nombre' in error.lower()
    
    def test_validate_invalid_email(self):
        """Verifica que rechaza emails inválidos"""
        validator = ValidateProductCSV()
        
        invalid_emails = ['notanemail', 'missing@', '@nodomain.com', 'spaces in@email.com']
        
        for invalid_email in invalid_emails:
            row = {
                'sku': '123456789',
                'name': 'Test Supplier',
                'address_line1': '123 Main St',
                'phone': '555-1234',
                'email': invalid_email,
                'country': 'Colombia'
            }
            
            is_valid, error = validator.validate_row_data(row, 2)
            
            assert is_valid is False, f"Should reject email: {invalid_email}"
            assert 'email' in error.lower()
    
    def test_validate_valid_emails(self):
        """Verifica que acepta emails válidos"""
        validator = ValidateProductCSV()
        
        valid_emails = [
            'test@example.com',
            'contact@company.co.uk',
            'info+sales@domain.com',
            'user.name@sub.domain.com'
        ]
        
        for valid_email in valid_emails:
            row = {
                'sku': '123456789',
                'name': 'Test Supplier',
                'address_line1': '123 Main St',
                'phone': '555-1234',
                'email': valid_email,
                'country': 'Colombia'
            }
            
            is_valid, error = validator.validate_row_data(row, 2)
            
            assert is_valid is True, f"Should accept email: {valid_email}"
    
    def test_validate_phone_too_short(self):
        """Verifica que rechaza teléfonos muy cortos"""
        validator = ValidateProductCSV()
        
        row = {
            'sku': '123456789',
            'name': 'Test Supplier',
            'address_line1': '123 Main St',
            'phone': '12345',  # Muy corto
            'email': 'test@test.com',
            'country': 'Colombia'
        }
        
        is_valid, error = validator.validate_row_data(row, 2)
        
        assert is_valid is False
        assert 'teléfono' in error.lower() or 'phone' in error.lower()
    
    def test_validate_address_too_short(self):
        """Verifica que rechaza direcciones muy cortas"""
        validator = ValidateProductCSV()
        
        row = {
            'sku': '123456789',
            'name': 'Test Supplier',
            'address_line1': '123',  # Muy corta
            'phone': '555-1234',
            'email': 'test@test.com',
            'country': 'Colombia'
        }
        
        is_valid, error = validator.validate_row_data(row, 2)
        
        assert is_valid is False
        assert 'dirección' in error.lower() or 'address' in error.lower()
    
    def test_validate_invalid_country(self):
        """Verifica que rechaza países no válidos"""
        validator = ValidateProductCSV()
        
        row = {
            'sku': '123456789',
            'name': 'Test Supplier',
            'address_line1': '123 Main St',
            'phone': '555-1234',
            'email': 'test@test.com',
            'country': 'InvalidCountry'
        }
        
        is_valid, error = validator.validate_row_data(row, 2)
        
        assert is_valid is False
        assert 'país' in error.lower() or 'country' in error.lower()
    
    def test_validate_invalid_currency(self):
        """Verifica que rechaza monedas inválidas"""
        validator = ValidateProductCSV()
        
        row = {
            'sku': '123456789',
            'name': 'Test Supplier',
            'address_line1': '123 Main St',
            'phone': '555-1234',
            'email': 'test@test.com',
            'country': 'Colombia',
            'currency': 'INVALID'
        }
        
        is_valid, error = validator.validate_row_data(row, 2)
        
        assert is_valid is False
        assert 'moneda' in error.lower() or 'currency' in error.lower()
    
    def test_validate_valid_currency(self):
        """Verifica que acepta monedas válidas"""
        validator = ValidateProductCSV()
        
        for currency in ['USD', 'COP', 'EUR']:
            row = {
                'sku': '123456789',
                'name': 'Test Supplier',
                'address_line1': '123 Main St',
                'phone': '555-1234',
                'email': 'test@test.com',
                'country': 'Colombia',
                'currency': currency
            }
            
            is_valid, error = validator.validate_row_data(row, 2)
            
            assert is_valid is True
    
    def test_validate_invalid_credit_limit(self):
        """Verifica que rechaza límites de crédito inválidos"""
        validator = ValidateProductCSV()
        
        row = {
            'sku': '123456789',
            'name': 'Test Supplier',
            'address_line1': '123 Main St',
            'phone': '555-1234',
            'email': 'test@test.com',
            'country': 'Colombia',
            'credit_limit': 'not-a-number'
        }
        
        is_valid, error = validator.validate_row_data(row, 2)
        
        assert is_valid is False
        assert 'crédito' in error.lower() or 'credit' in error.lower()
    
    def test_validate_negative_credit_limit(self):
        """Verifica que rechaza límites de crédito negativos"""
        validator = ValidateProductCSV()
        
        row = {
            'sku': '123456789',
            'name': 'Test Supplier',
            'address_line1': '123 Main St',
            'phone': '555-1234',
            'email': 'test@test.com',
            'country': 'Colombia',
            'credit_limit': '-1000'
        }
        
        is_valid, error = validator.validate_row_data(row, 2)
        
        assert is_valid is False
        assert 'negativo' in error.lower()
    
    def test_validate_valid_boolean_values(self):
        """Verifica que acepta valores booleanos válidos"""
        validator = ValidateProductCSV()
        
        boolean_values = ['true', 'false', '1', '0', 'yes', 'no', 'si', 'sí', 't', 'f', 'y', 'n']
        
        for bool_val in boolean_values:
            row = {
                'sku': '123456789',
                'name': 'Test Supplier',
                'address_line1': '123 Main St',
                'phone': '555-1234',
                'email': 'test@test.com',
                'country': 'Colombia',
                'is_certified': bool_val,
                'is_active': bool_val
            }
            
            is_valid, error = validator.validate_row_data(row, 2)
            
            assert is_valid is True, f"Should accept boolean value: {bool_val}"
    
    def test_validate_invalid_date_format(self):
        """Verifica que rechaza fechas con formato inválido"""
        validator = ValidateProductCSV()
        
        invalid_dates = ['2024/01/15', '15-01-2024', 'invalid-date', '2024-13-01']
        
        for invalid_date in invalid_dates:
            row = {
                'sku': '123456789',
                'name': 'Test Supplier',
                'address_line1': '123 Main St',
                'phone': '555-1234',
                'email': 'test@test.com',
                'country': 'Colombia',
                'certification_date': invalid_date
            }
            
            is_valid, error = validator.validate_row_data(row, 2)
            
            assert is_valid is False, f"Should reject date: {invalid_date}"
    
    def test_validate_valid_date_format(self):
        """Verifica que acepta fechas con formato válido"""
        validator = ValidateProductCSV()
        
        row = {
            'sku': '123456789',
            'name': 'Test Supplier',
            'address_line1': '123 Main St',
            'phone': '555-1234',
            'email': 'test@test.com',
            'country': 'Colombia',
            'certification_date': '2024-01-15',
            'certification_expiry': '2025-01-15'
        }
        
        is_valid, error = validator.validate_row_data(row, 2)
        
        assert is_valid is True


class TestValidateBusinessRules:
    """Tests para el método validate_business_rules"""
    
    def test_validate_unique_sku(self, app):
        """Verifica que rechaza sku duplicados"""
        from src.session import db
        
        validator = ValidateProductCSV()
        
        with app.app_context():
            # Crear supplier existente
            existing_supplier = Supplier(
                name='Existing Supplier',
                sku='123456789',
                legal_name='Existing Supplier LLC',
                country='Colombia',
                email='existing@test.com',
                phone='555-0000',
                address_line1='123 Existing St'
            )
            db.session.add(existing_supplier)
            db.session.commit()
            
            # Intentar validar un supplier con el mismo sku
            row = {
                'sku': '123456789',
                'name': 'New Supplier',
                'address_line1': '456 New St',
                'phone': '555-9999',
                'email': 'new@test.com',
                'country': 'Colombia'
            }
            
            is_valid, error = validator.validate_business_rules(row, 2)
            
            assert is_valid is False
            assert 'existe' in error.lower() or 'ruc' in error.lower() or 'sku' in error.lower()
    
    def test_validate_new_sku(self, app):
        """Verifica que acepta sku únicos"""
        from src.session import db
        
        validator = ValidateProductCSV()
        
        with app.app_context():
            row = {
                'sku': 'NEW-TAX-ID-999',
                'name': 'New Supplier',
                'address_line1': '456 New St',
                'phone': '555-9999',
                'email': 'new@test.com',
                'country': 'Colombia'
            }
            
            is_valid, error = validator.validate_business_rules(row, 2)
            
            assert is_valid is True
            assert error is None


class TestParseCSVToList:
    """Tests para el método parse_csv_to_list"""
    
    def test_parse_valid_csv(self):
        """Verifica que parsea correctamente un CSV válido"""
        validator = ValidateProductCSV()
        
        csv_content = b"sku,name,email\n123,Test Supplier,test@test.com\n456,Another Supplier,another@test.com\n"
        
        result = validator.parse_csv_to_list(csv_content)
        
        assert len(result) == 2
        assert result[0]['sku'] == '123'
        assert result[0]['name'] == 'Test Supplier'
        assert result[1]['sku'] == '456'
    
    def test_parse_csv_with_bom(self):
        """Verifica que parsea CSV con BOM"""
        validator = ValidateProductCSV()
        
        csv_content = b"\xef\xbb\xbfsku,name\n123,Test\n"
        
        result = validator.parse_csv_to_list(csv_content)
        
        assert len(result) == 1
        assert result[0]['sku'] == '123'
