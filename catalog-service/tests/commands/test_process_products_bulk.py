"""
Tests para ProcessProductsBulk command.
Cubre procesamiento en background, creación de productos y parseo de valores.
"""
import pytest
import threading
import time
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock
from src.commands.process_products_bulk import ProcessProductsBulk
from src.models.product import Product
from src.models.supplier import Supplier
from src.models.bulk_upload_job import BulkUploadJob, JobStatus
from src.session import db


class TestStartProcessing:
    """Tests para el método start_processing"""
    
    def test_start_processing_creates_thread(self, app):
        """Verifica que start_processing crea y arranca un thread"""
        processor = ProcessProductsBulk(app)
        
        with patch.object(threading, 'Thread') as mock_thread:
            mock_thread_instance = Mock()
            mock_thread.return_value = mock_thread_instance
            
            csv_data = [{'sku': 'TEST-001', 'name': 'Test Product'}]
            processor.start_processing('job-123', csv_data)
            
            # Verifica que Thread fue llamado con los argumentos correctos
            mock_thread.assert_called_once()
            call_kwargs = mock_thread.call_args[1]
            assert call_kwargs['target'] == processor._process_in_background
            assert call_kwargs['args'] == ('job-123', csv_data)
            assert call_kwargs['daemon'] is True
            
            # Verifica que el thread fue iniciado
            mock_thread_instance.start.assert_called_once()


class TestProcessInBackground:
    """Tests para el método _process_in_background"""
    
    def test_process_job_not_found(self, app, capsys):
        """Verifica que imprime error si el job no existe"""
        processor = ProcessProductsBulk(app)
        
        with app.app_context():
            processor._process_in_background('nonexistent-job', [])
            
            captured = capsys.readouterr()
            assert 'ERROR: Job nonexistent-job not found' in captured.out
    
    def test_process_successful_product_creation(self, app):
        """Verifica procesamiento exitoso de productos válidos"""
        processor = ProcessProductsBulk(app)
        
        with app.app_context():
            # Crear supplier
            supplier = Supplier(
                name='Test Supplier',
                tax_id='123456789',
                legal_name='Test Supplier LLC',
                country='Colombia',
                email='supplier@test.com'
            )
            db.session.add(supplier)
            db.session.commit()
            
            # Crear job
            job = BulkUploadJob(filename='test.csv', total_rows=1)
            db.session.add(job)
            db.session.commit()
            job_id = job.job_id
            
            # Datos del CSV
            csv_data = [{
                'sku': 'TEST-001',
                'name': 'Test Product',
                'category': 'Medicamentos',
                'unit_price': '100.50',
                'currency': 'USD',
                'unit_of_measure': 'Unidad',
                'supplier_id': str(supplier.id),
                'requires_cold_chain': 'false',
                'requires_prescription': 'false',
                'is_active': 'true'
            }]
            
            # Procesar
            processor._process_in_background(job_id, csv_data)
            
            # Refrescar job desde la DB
            db.session.expire_all()
            job = BulkUploadJob.query.filter_by(job_id=job_id).first()
            assert job.status == JobStatus.COMPLETED
            assert job.get_successful_rows() == 1
            assert job.get_failed_rows() == 0
            assert job.get_processed_rows() == 1
            
            # Verificar producto creado
            product = Product.query.filter_by(sku='TEST-001').first()
            assert product is not None
            assert product.name == 'Test Product'
            assert product.unit_price == Decimal('100.50')
    
    def test_process_with_invalid_data_marks_row_failed(self, app):
        """Verifica que datos inválidos marcan la fila como fallida"""
        processor = ProcessProductsBulk(app)
        
        with app.app_context():
            # Crear job
            job = BulkUploadJob(filename='test.csv', total_rows=1)
            db.session.add(job)
            db.session.commit()
            job_id = job.job_id
            
            # Datos inválidos - precio inválido
            csv_data = [{
                'sku': 'TEST-002',
                'name': 'Invalid Product',
                'category': 'Medicamentos',
                'unit_price': 'not-a-number',  # Precio inválido
                'currency': 'USD',
                'unit_of_measure': 'Unidad',
                'supplier_id': '1',
                'requires_cold_chain': 'false',
                'requires_prescription': 'false'
            }]
            
            # Procesar
            processor._process_in_background(job_id, csv_data)
            
            # Refrescar job desde la DB
            db.session.expire_all()
            job = BulkUploadJob.query.filter_by(job_id=job_id).first()
            assert job.status == JobStatus.COMPLETED
            assert job.get_failed_rows() == 1
            assert job.get_successful_rows() == 0
            assert len(job.get_errors()) > 0
    
    def test_process_commits_every_50_rows(self, app):
        """Verifica que hace commit cada 50 productos"""
        processor = ProcessProductsBulk(app)
        
        with app.app_context():
            # Crear supplier
            supplier = Supplier(
                name='Test Supplier',
                tax_id='123456789',
                legal_name='Test Supplier LLC',
                country='Colombia',
                email='supplier@test.com'
            )
            db.session.add(supplier)
            db.session.commit()
            
            # Crear job con 51 filas
            job = BulkUploadJob(filename='test.csv', total_rows=51)
            db.session.add(job)
            db.session.commit()
            job_id = job.job_id
            
            # Crear 51 productos
            csv_data = []
            for i in range(51):
                csv_data.append({
                    'sku': f'TEST-{i:03d}',
                    'name': f'Product {i}',
                    'category': 'Medicamentos',
                    'unit_price': '100.00',
                    'currency': 'USD',
                    'unit_of_measure': 'Unidad',
                    'supplier_id': str(supplier.id),
                    'requires_cold_chain': 'false',
                    'requires_prescription': 'false'
                })
            
            # Procesar
            processor._process_in_background(job_id, csv_data)
            
            # Refrescar job desde la DB
            db.session.expire_all()
            job = BulkUploadJob.query.filter_by(job_id=job_id).first()
            assert job.get_successful_rows() == 51
            assert job.get_processed_rows() == 51
            assert job.status == JobStatus.COMPLETED


class TestCreateProductFromRow:
    """Tests para el método _create_product_from_row"""
    
    def test_create_product_with_all_fields(self, app):
        """Verifica creación de producto con todos los campos"""
        processor = ProcessProductsBulk(app)
        
        row = {
            'sku': 'PROD-001',
            'name': 'Complete Product',
            'description': 'Full description',
            'category': 'Medicamentos',
            'subcategory': 'Antibióticos',
            'unit_price': '250.75',
            'currency': 'usd',
            'unit_of_measure': 'Caja',
            'supplier_id': '1',
            'requires_cold_chain': 'true',
            'storage_temperature_min': '2.5',
            'storage_temperature_max': '8.0',
            'storage_humidity_max': '60.5',
            'sanitary_registration': 'INVIMA-2024-001',
            'requires_prescription': 'yes',
            'regulatory_class': 'II',
            'weight_kg': '0.5',
            'length_cm': '10.5',
            'width_cm': '5.0',
            'height_cm': '3.2',
            'manufacturer': 'PharmaCorp',
            'country_of_origin': 'Colombia',
            'barcode': '7501234567890',
            'image_url': 'https://example.com/image.jpg',
            'is_active': '1',
            'is_discontinued': 'false'
        }
        
        product = processor._create_product_from_row(row)
        
        assert product.sku == 'PROD-001'
        assert product.name == 'Complete Product'
        assert product.description == 'Full description'
        assert product.category == 'Medicamentos'
        assert product.subcategory == 'Antibióticos'
        assert product.unit_price == Decimal('250.75')
        assert product.currency == 'USD'
        assert product.unit_of_measure == 'Caja'
        assert product.supplier_id == 1
        assert product.requires_cold_chain is True
        assert product.storage_temperature_min == 2.5
        assert product.storage_temperature_max == 8.0
        assert product.storage_humidity_max == Decimal('60.5')
        assert product.sanitary_registration == 'INVIMA-2024-001'
        assert product.requires_prescription is True
        assert product.regulatory_class == 'II'
        assert product.weight_kg == Decimal('0.5')
        assert product.length_cm == Decimal('10.5')
        assert product.width_cm == Decimal('5.0')
        assert product.height_cm == Decimal('3.2')
        assert product.manufacturer == 'PharmaCorp'
        assert product.country_of_origin == 'Colombia'
        assert product.barcode == '7501234567890'
        assert product.image_url == 'https://example.com/image.jpg'
        assert product.is_active is True
        assert product.is_discontinued is False
    
    def test_create_product_with_minimal_fields(self, app):
        """Verifica creación de producto con campos mínimos"""
        processor = ProcessProductsBulk(app)
        
        row = {
            'sku': 'MIN-001',
            'name': 'Minimal Product',
            'category': 'Equipos',
            'unit_price': '100.00',
            'currency': 'COP',
            'unit_of_measure': 'Unidad',
            'supplier_id': '5'
        }
        
        product = processor._create_product_from_row(row)
        
        assert product.sku == 'MIN-001'
        assert product.name == 'Minimal Product'
        assert product.description is None
        assert product.subcategory is None
        assert product.unit_price == Decimal('100.00')
        assert product.currency == 'COP'
        assert product.requires_cold_chain is False
        assert product.storage_temperature_min is None
        assert product.storage_temperature_max is None
        assert product.is_active is True  # Default
        assert product.is_discontinued is False  # Default
    
    def test_create_product_strips_whitespace(self, app):
        """Verifica que elimina espacios en blanco"""
        processor = ProcessProductsBulk(app)
        
        row = {
            'sku': '  PROD-002  ',
            'name': '  Product Name  ',
            'category': '  Medicamentos  ',
            'unit_price': '100.00',
            'currency': '  usd  ',
            'unit_of_measure': '  Unidad  ',
            'supplier_id': '1'
        }
        
        product = processor._create_product_from_row(row)
        
        assert product.sku == 'PROD-002'
        assert product.name == 'Product Name'
        assert product.category == 'Medicamentos'
        assert product.currency == 'USD'
        assert product.unit_of_measure == 'Unidad'
    
    def test_create_product_converts_empty_strings_to_none(self, app):
        """Verifica que convierte strings vacíos a None"""
        processor = ProcessProductsBulk(app)
        
        row = {
            'sku': 'PROD-003',
            'name': 'Product',
            'description': '',
            'category': 'Medicamentos',
            'subcategory': '  ',
            'unit_price': '100.00',
            'currency': 'USD',
            'unit_of_measure': 'Unidad',
            'supplier_id': '1',
            'sanitary_registration': '',
            'regulatory_class': '   ',
            'manufacturer': '',
            'country_of_origin': '',
            'barcode': '',
            'image_url': ''
        }
        
        product = processor._create_product_from_row(row)
        
        assert product.description is None
        assert product.subcategory is None
        assert product.sanitary_registration is None
        assert product.regulatory_class is None
        assert product.manufacturer is None
        assert product.country_of_origin is None
        assert product.barcode is None
        assert product.image_url is None


class TestParseBoolean:
    """Tests para el método _parse_boolean"""
    
    def test_parse_true_values(self, app):
        """Verifica que parsea valores verdaderos correctamente"""
        processor = ProcessProductsBulk(app)
        
        true_values = ['true', 'True', 'TRUE', '1', 'yes', 'Yes', 'YES', 
                       'si', 'Si', 'SI', 'sí', 'Sí', 'SÍ', 't', 'T', 'y', 'Y']
        
        for value in true_values:
            assert processor._parse_boolean(value) is True, f"Failed for value: {value}"
    
    def test_parse_false_values(self, app):
        """Verifica que parsea valores falsos correctamente"""
        processor = ProcessProductsBulk(app)
        
        false_values = ['false', 'False', 'FALSE', '0', 'no', 'No', 'NO', 
                        'f', 'F', 'n', 'N', 'anything', '']
        
        for value in false_values:
            assert processor._parse_boolean(value) is False, f"Failed for value: {value}"
    
    def test_parse_none_returns_false(self, app):
        """Verifica que None retorna False"""
        processor = ProcessProductsBulk(app)
        
        assert processor._parse_boolean(None) is False
    
    def test_parse_with_whitespace(self, app):
        """Verifica que maneja espacios en blanco"""
        processor = ProcessProductsBulk(app)
        
        assert processor._parse_boolean('  true  ') is True
        assert processor._parse_boolean('  false  ') is False


class TestParseFloat:
    """Tests para el método _parse_float"""
    
    def test_parse_valid_float(self, app):
        """Verifica parseo de float válido"""
        processor = ProcessProductsBulk(app)
        
        assert processor._parse_float('3.14') == 3.14
        assert processor._parse_float('100.0') == 100.0
        assert processor._parse_float('-5.5') == -5.5
        assert processor._parse_float('0') == 0.0
    
    def test_parse_empty_returns_none(self, app):
        """Verifica que valores vacíos retornan None"""
        processor = ProcessProductsBulk(app)
        
        assert processor._parse_float(None) is None
        assert processor._parse_float('') is None
        assert processor._parse_float('   ') is None
    
    def test_parse_invalid_returns_none(self, app):
        """Verifica que valores inválidos retornan None"""
        processor = ProcessProductsBulk(app)
        
        assert processor._parse_float('invalid') is None
        assert processor._parse_float('abc123') is None


class TestParseDecimal:
    """Tests para el método _parse_decimal"""
    
    def test_parse_valid_decimal(self, app):
        """Verifica parseo de Decimal válido"""
        processor = ProcessProductsBulk(app)
        
        assert processor._parse_decimal('3.14') == Decimal('3.14')
        assert processor._parse_decimal('100.50') == Decimal('100.50')
        assert processor._parse_decimal('-5.5') == Decimal('-5.5')
        assert processor._parse_decimal('0') == Decimal('0')
    
    def test_parse_empty_returns_none(self, app):
        """Verifica que valores vacíos retornan None"""
        processor = ProcessProductsBulk(app)
        
        assert processor._parse_decimal(None) is None
        assert processor._parse_decimal('') is None
        assert processor._parse_decimal('   ') is None
    
    def test_parse_invalid_returns_none(self, app):
        """Verifica que valores inválidos retornan None"""
        processor = ProcessProductsBulk(app)
        
        assert processor._parse_decimal('invalid') is None
        assert processor._parse_decimal('abc123') is None
