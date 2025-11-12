"""
Tests para el blueprint de carga masiva de productos (bulk_upload.py)
Cobertura 100% de todos los endpoints y casos de uso.
"""
import pytest
import io
import csv
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from src.models.bulk_upload_job import BulkUploadJob, JobStatus
from src.models.product import Product
from src.models.supplier import Supplier
from src.errors.errors import ApiError


class TestBulkUploadTemplate:
    """Tests para el endpoint GET /template"""
    
    def test_download_template_success(self, client):
        """Debe descargar una plantilla CSV con headers y ejemplos"""
        response = client.get('/api/products/bulk-upload/template')
        
        assert response.status_code == 200
        assert response.mimetype == 'text/csv'
        assert 'plantilla_productos.csv' in response.headers.get('Content-Disposition', '')
        
        # Verificar contenido del CSV
        content = response.data.decode('utf-8-sig')
        lines = content.strip().split('\n')
        
        # Verificar headers
        assert 'sku' in lines[0]
        assert 'name' in lines[0]
        assert 'storage_humidity_max' in lines[0]
        assert 'image_url' in lines[0]
        assert 'is_discontinued' in lines[0]
        
        # Verificar que tiene 3 filas de ejemplo + header = 4 líneas
        assert len(lines) == 4
    
    def test_download_template_has_correct_columns(self, client):
        """Debe tener todas las 26 columnas del modelo Product"""
        response = client.get('/api/products/bulk-upload/template')
        
        content = response.data.decode('utf-8-sig')
        reader = csv.reader(io.StringIO(content))
        headers = next(reader)
        
        expected_columns = [
            'sku', 'name', 'description', 'category', 'subcategory',
            'unit_price', 'currency', 'unit_of_measure', 'supplier_id',
            'requires_cold_chain', 'storage_temperature_min', 'storage_temperature_max', 
            'storage_humidity_max', 'sanitary_registration', 'requires_prescription', 
            'regulatory_class', 'weight_kg', 'length_cm', 'width_cm', 'height_cm',
            'manufacturer', 'country_of_origin', 'barcode', 'image_url',
            'is_active', 'is_discontinued'
        ]
        
        assert headers == expected_columns
    
    def test_download_template_examples_valid(self, client):
        """Los ejemplos en la plantilla deben ser válidos"""
        response = client.get('/api/products/bulk-upload/template')
        
        content = response.data.decode('utf-8-sig')
        reader = csv.reader(io.StringIO(content))
        headers = next(reader)
        
        example_rows = list(reader)
        assert len(example_rows) == 3
        
        # Verificar primera fila (vacuna)
        assert example_rows[0][0] == 'VAC-FLU-2025'
        assert example_rows[0][9] == 'true'  # requires_cold_chain (índice 9)
        assert example_rows[0][12] == '60'  # storage_humidity_max
        
        # Verificar segunda fila (estetoscopio)
        assert example_rows[1][0] == 'STET-DIG-PRO'
        assert example_rows[1][9] == 'false'  # requires_cold_chain


class TestBulkUploadCSV:
    """Tests para el endpoint POST /"""
    
    def test_upload_csv_no_file(self, client):
        """Debe retornar 400 si no se envía archivo"""
        response = client.post('/api/products/bulk-upload')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'No se envió ningún archivo' in data['error']
    
    def test_upload_csv_empty_filename(self, client):
        """Debe retornar 400 si el archivo no tiene nombre"""
        data = {
            'file': (io.BytesIO(b''), '')
        }
        response = client.post(
            '/api/products/bulk-upload',
            data=data,
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'sin nombre' in data['error']
    
    def test_upload_csv_invalid_structure(self, client):
        """Debe retornar 400 si el CSV tiene estructura inválida"""
        csv_content = "invalid,headers\ndata1,data2"
        data = {
            'file': (io.BytesIO(csv_content.encode('utf-8')), 'test.csv')
        }
        
        response = client.post(
            '/api/products/bulk-upload',
            data=data,
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'inválido' in data['error']
    
    def test_upload_csv_success(self, client, app, sample_supplier):
        """Debe crear job y retornar 202 con CSV válido"""
        # Crear CSV válido
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            'sku', 'name', 'description', 'category', 'subcategory',
            'unit_price', 'currency', 'unit_of_measure', 'supplier_id',
            'requires_cold_chain', 'storage_temperature_min', 'storage_temperature_max',
            'storage_humidity_max', 'sanitary_registration', 'requires_prescription',
            'regulatory_class', 'weight_kg', 'length_cm', 'width_cm', 'height_cm',
            'manufacturer', 'country_of_origin', 'barcode', 'image_url',
            'is_active', 'is_discontinued'
        ])
        writer.writerow([
            'TEST-001', 'Producto Test', 'Descripción', 'Medicamentos', 'Generales',
            '10.50', 'USD', 'unidad', str(sample_supplier.id),
            'false', '', '', '', 'REG-123', 'false', 'Clase I',
            '', '', '', '', 'Test Manufacturer', 'Colombia', '1234567890123',
            '', 'true', 'false'
        ])
        
        csv_bytes = output.getvalue().encode('utf-8')
        
        with patch('src.commands.process_products_bulk.ProcessProductsBulk.start_processing') as mock_process:
            data = {
                'file': (io.BytesIO(csv_bytes), 'productos.csv'),
                'created_by': 'test_user'
            }
            
            response = client.post(
                '/api/products/bulk-upload',
                data=data,
                content_type='multipart/form-data'
            )
        
        assert response.status_code == 202
        data = response.get_json()
        assert 'job_id' in data
        assert data['status'] == JobStatus.PENDING
        assert data['filename'] == 'productos.csv'
        assert data['total_rows'] == 1
        assert 'Procesando' in data['message']
        
        # Verificar que se llamó start_processing
        mock_process.assert_called_once()
    
    def test_upload_csv_duplicate_file_hash(self, client, app, sample_supplier):
        """Debe detectar archivo duplicado por hash"""
        # Crear CSV
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            'sku', 'name', 'description', 'category', 'subcategory',
            'unit_price', 'currency', 'unit_of_measure', 'supplier_id',
            'requires_cold_chain', 'storage_temperature_min', 'storage_temperature_max',
            'storage_humidity_max', 'sanitary_registration', 'requires_prescription',
            'regulatory_class', 'weight_kg', 'length_cm', 'width_cm', 'height_cm',
            'manufacturer', 'country_of_origin', 'barcode', 'image_url',
            'is_active', 'is_discontinued'
        ])
        writer.writerow([
            'TEST-002', 'Producto Test 2', 'Descripción', 'Medicamentos', 'Generales',
            '20.00', 'USD', 'unidad', str(sample_supplier.id),
            'false', '', '', '', 'REG-456', 'false', 'Clase I',
            '', '', '', '', 'Test Manufacturer', 'Colombia', '1234567890124',
            '', 'true', 'false'
        ])
        
        csv_bytes = output.getvalue().encode('utf-8')
        
        # Crear job existente con mismo hash
        import hashlib
        file_hash = hashlib.sha256(csv_bytes).hexdigest()
        
        with app.app_context():
            existing_job = BulkUploadJob(
                filename='existing.csv',
                total_rows=1,
                created_by='other_user',
                file_size_bytes=len(csv_bytes),
                file_hash=file_hash
            )
            existing_job.status = JobStatus.PROCESSING
            from src.session import db
            db.session.add(existing_job)
            db.session.commit()
            existing_job_id = existing_job.job_id
        
        # Intentar subir mismo archivo
        data = {
            'file': (io.BytesIO(csv_bytes), 'duplicado.csv')
        }
        
        response = client.post(
            '/api/products/bulk-upload',
            data=data,
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'warning' in data
        assert 'ya está siendo procesado' in data['warning']
        assert data['existing_job']['job_id'] == existing_job_id
    
    def test_upload_csv_with_created_by(self, client, app, sample_supplier):
        """Debe usar el campo created_by si se proporciona"""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            'sku', 'name', 'description', 'category', 'subcategory',
            'unit_price', 'currency', 'unit_of_measure', 'supplier_id',
            'requires_cold_chain', 'storage_temperature_min', 'storage_temperature_max',
            'storage_humidity_max', 'sanitary_registration', 'requires_prescription',
            'regulatory_class', 'weight_kg', 'length_cm', 'width_cm', 'height_cm',
            'manufacturer', 'country_of_origin', 'barcode', 'image_url',
            'is_active', 'is_discontinued'
        ])
        writer.writerow([
            'TEST-003', 'Test 3', 'Desc', 'Medicamentos', 'Gen',
            '5.00', 'USD', 'unidad', str(sample_supplier.id),
            'false', '', '', '', 'REG-789', 'false', 'Clase I',
            '', '', '', '', 'Mfg', 'Col', '1234567890125',
            '', 'true', 'false'
        ])
        
        csv_bytes = output.getvalue().encode('utf-8')
        
        with patch('src.commands.process_products_bulk.ProcessProductsBulk.start_processing'):
            data = {
                'file': (io.BytesIO(csv_bytes), 'test.csv'),
                'created_by': 'john_doe'
            }
            
            response = client.post(
                '/api/products/bulk-upload',
                data=data,
                content_type='multipart/form-data'
            )
        
        assert response.status_code == 202
        
        # Verificar en BD
        with app.app_context():
            from src.session import db
            job = BulkUploadJob.query.filter_by(filename='test.csv').first()
            assert job.created_by == 'john_doe'



class TestGetUploadHistory:
    """Tests para el endpoint GET /history"""
    
    def test_get_history_empty(self, client, app):
        """Debe retornar lista vacía si no hay jobs"""
        response = client.get('/api/products/bulk-upload/history')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['jobs'] == []
        assert data['total'] == 0
        assert data['limit'] == 50
        assert data['offset'] == 0
    
    def test_get_history_with_jobs(self, client, app):
        """Debe retornar lista de jobs ordenados por fecha"""
        with app.app_context():
            from src.session import db
            for i in range(3):
                job = BulkUploadJob(
                    filename=f'test_{i}.csv',
                    total_rows=10,
                    created_by=f'user_{i}',
                    file_size_bytes=1024,
                    file_hash=f'hash_{i}'
                )
                db.session.add(job)
            db.session.commit()
        
        response = client.get('/api/products/bulk-upload/history')
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['jobs']) == 3
        assert data['total'] == 3
    
    def test_get_history_with_status_filter(self, client, app):
        """Debe filtrar por status"""
        with app.app_context():
            from src.session import db
            job1 = BulkUploadJob(
                filename='pending.csv',
                total_rows=5,
                created_by='user1',
                file_size_bytes=512,
                file_hash='h1'
            )
            job1.status = JobStatus.PENDING
            
            job2 = BulkUploadJob(
                filename='completed.csv',
                total_rows=10,
                created_by='user2',
                file_size_bytes=1024,
                file_hash='h2'
            )
            job2.status = JobStatus.COMPLETED
            
            db.session.add_all([job1, job2])
            db.session.commit()
        
        response = client.get('/api/products/bulk-upload/history?status=completed')
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['jobs']) == 1
        assert data['jobs'][0]['filename'] == 'completed.csv'
    
    def test_get_history_with_created_by_filter(self, client, app):
        """Debe filtrar por created_by"""
        with app.app_context():
            from src.session import db
            job1 = BulkUploadJob(
                filename='file1.csv',
                total_rows=5,
                created_by='alice',
                file_size_bytes=512,
                file_hash='ha1'
            )
            job2 = BulkUploadJob(
                filename='file2.csv',
                total_rows=10,
                created_by='bob',
                file_size_bytes=1024,
                file_hash='ha2'
            )
            db.session.add_all([job1, job2])
            db.session.commit()
        
        response = client.get('/api/products/bulk-upload/history?created_by=alice')
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['jobs']) == 1
        assert data['jobs'][0]['filename'] == 'file1.csv'
    
    def test_get_history_with_pagination(self, client, app):
        """Debe paginar correctamente"""
        with app.app_context():
            from src.session import db
            for i in range(10):
                job = BulkUploadJob(
                    filename=f'file_{i}.csv',
                    total_rows=5,
                    created_by='user',
                    file_size_bytes=512,
                    file_hash=f'hash_{i}'
                )
                db.session.add(job)
            db.session.commit()
        
        response = client.get('/api/products/bulk-upload/history?limit=3&offset=2')
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['jobs']) == 3
        assert data['limit'] == 3
        assert data['offset'] == 2
        assert data['total'] == 10
    
    def test_get_history_limit_max_100(self, client, app):
        """Debe limitar a máximo 100 registros"""
        response = client.get('/api/products/bulk-upload/history?limit=500')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['limit'] == 100
    
    def test_get_history_invalid_limit(self, client):
        """Debe retornar 400 si limit no es número"""
        response = client.get('/api/products/bulk-upload/history?limit=invalid')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'inválidos' in data['error']


def test_get_upload_history_exception_in_to_summary_dict(client, app, monkeypatch):
    """Debe retornar 500 si ocurre excepción en job.to_summary_dict()"""
    with app.app_context():
        from src.session import db
        job = BulkUploadJob(
            filename='test.csv',
            total_rows=1,
            created_by='user',
            file_size_bytes=10,
            file_hash='hash'
        )
        db.session.add(job)
        db.session.commit()
    monkeypatch.setattr("src.models.bulk_upload_job.BulkUploadJob.to_summary_dict", lambda self: (_ for _ in ()).throw(Exception("Error generado")))
    response = client.get('/api/products/bulk-upload/history')
    assert response.status_code == 500
    data = response.get_json()
    assert 'Error al obtener historial' in data['error']


class TestDownloadErrors:
    """Tests para el endpoint GET /{job_id}/errors"""
    

    def test_download_errors_no_errors(self, client, app):
        """Debe retornar 404 si el job no tiene errores"""
        with app.app_context():
            from src.session import db
            job = BulkUploadJob(
                filename='no_errors.csv',
                total_rows=5,
                created_by='user',
                file_size_bytes=512,
                file_hash='hash_noerr'
            )
            db.session.add(job)
            db.session.commit()
            job_id = job.job_id

        response = client.get(f'/api/products/bulk-upload/{job_id}/errors')
        assert response.status_code == 404
        data = response.get_json()
        assert 'no tiene errores' in data['error']
    
    def test_download_errors_success(self, client, app):
        """Debe descargar CSV con errores"""
        with app.app_context():
            from src.session import db
            job = BulkUploadJob(
                filename='failed.csv',
                total_rows=10,
                created_by='user',
                file_size_bytes=1024,
                file_hash='hash2'
            )
            job.add_error(1, {'sku': 'TEST-001', 'name': 'Producto 1'}, 'SKU duplicado')
            job.add_error(3, {'sku': 'TEST-002', 'name': 'Producto 2'}, 'Precio inválido')
            db.session.add(job)
            db.session.commit()
            job_id = job.job_id
        
        response = client.get(f'/api/products/bulk-upload/{job_id}/errors')
        
        assert response.status_code == 200
        assert response.mimetype == 'text/csv'
        assert 'errores_failed.csv' in response.headers.get('Content-Disposition', '')
        
        # Verificar contenido
        content = response.data.decode('utf-8-sig')
        lines = content.strip().split('\n')
        
        assert len(lines) == 3  # header + 2 errores
        assert 'row_number' in lines[0]
        assert 'error_message' in lines[0]
        assert 'SKU duplicado' in content
        assert 'Precio inválido' in content
    
    def test_download_errors_exception(self, client, app, monkeypatch):
        """Debe retornar 500 si ocurre excepción en download_errors"""
        with app.app_context():
            from src.session import db
            job = BulkUploadJob(
                filename='err.csv',
                total_rows=1,
                created_by='user',
                file_size_bytes=10,
                file_hash='errhash'
            )
            db.session.add(job)
            db.session.commit()
            job_id = job.job_id
        monkeypatch.setattr("src.models.bulk_upload_job.BulkUploadJob.get_errors", lambda self: (_ for _ in ()).throw(Exception("Error generado")))
        response = client.get(f'/api/products/bulk-upload/{job_id}/errors')
        assert response.status_code == 500
        data = response.get_json()
        assert 'Error al generar archivo de errores' in data['error']


class TestCancelJob:
    """Tests para el endpoint POST /{job_id}/cancel"""
    
    def test_cancel_job_not_found(self, client):
        """Debe retornar 404 si el job no existe"""
        response = client.post('/api/products/bulk-upload/00000000-0000-0000-0000-000000000000/cancel')
        
        assert response.status_code == 404
        data = response.get_json()
        assert 'no encontrado' in data['error']
    
    def test_cancel_job_success(self, client, app):
        """Debe cancelar job en estado PENDING"""
        with app.app_context():
            from src.session import db
            job = BulkUploadJob(
                filename='cancel_me.csv',
                total_rows=5,
                created_by='user',
                file_size_bytes=512,
                file_hash='hash3'
            )
            # Status es PENDING por default
            db.session.add(job)
            db.session.commit()
            job_id = job.job_id
        
        response = client.post(f'/api/products/bulk-upload/{job_id}/cancel')
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'cancelado exitosamente' in data['message']
        assert data['job']['status'] == JobStatus.CANCELLED
        
        # Verificar en BD
        with app.app_context():
            from src.session import db
            job = BulkUploadJob.query.filter_by(job_id=job_id).first()
            assert job.status == JobStatus.CANCELLED
    
    def test_cancel_job_cannot_cancel_completed(self, client, app):
        """No debe cancelar job COMPLETED"""
        with app.app_context():
            from src.session import db
            job = BulkUploadJob(
                filename='completed.csv',
                total_rows=5,
                created_by='user',
                file_size_bytes=512,
                file_hash='hash4'
            )
            job.status = JobStatus.COMPLETED
            db.session.add(job)
            db.session.commit()
            job_id = job.job_id
        
        response = client.post(f'/api/products/bulk-upload/{job_id}/cancel')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'no puede ser cancelado' in data['error']
    
    def test_cancel_job_cannot_cancel_processing(self, client, app):
        """No debe cancelar job PROCESSING"""
        with app.app_context():
            from src.session import db
            job = BulkUploadJob(
                filename='processing.csv',
                total_rows=10,
                created_by='user',
                file_size_bytes=1024,
                file_hash='hash5'
            )
            job.status = JobStatus.PROCESSING
            db.session.add(job)
            db.session.commit()
            job_id = job.job_id
        
        response = client.post(f'/api/products/bulk-upload/{job_id}/cancel')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'no puede ser cancelado' in data['error']
    
    def test_cancel_job_exception(self, client, app, monkeypatch):
        """Debe retornar 500 si ocurre excepción en cancel_job"""
        with app.app_context():
            from src.session import db
            job = BulkUploadJob(
                filename='cancel.csv',
                total_rows=1,
                created_by='user',
                file_size_bytes=10,
                file_hash='cancelhash'
            )
            db.session.add(job)
            db.session.commit()
            job_id = job.job_id
        monkeypatch.setattr("src.models.bulk_upload_job.BulkUploadJob.can_be_cancelled", lambda self: (_ for _ in ()).throw(Exception("Error generado")))
        response = client.post(f'/api/products/bulk-upload/{job_id}/cancel')
        assert response.status_code == 500
        data = response.get_json()
        assert 'Error al cancelar job' in data['error']


class TestGetUploadStats:
    """Tests para el endpoint GET /stats"""
    
    def test_get_stats_empty(self, client):
        """Debe retornar stats vacías si no hay jobs"""
        response = client.get('/api/products/bulk-upload/stats')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['total_jobs'] == 0
        assert data['completed'] == 0
        assert data['failed'] == 0
        assert data['in_progress'] == 0
        assert data['cancelled'] == 0
        assert data['total_products_imported'] == 0
        assert data['average_success_rate'] == 0.0
    
    def test_get_stats_with_jobs(self, client, app):
        """Debe calcular stats correctamente"""
        with app.app_context():
            from src.session import db
            
            # Job completado exitoso
            job1 = BulkUploadJob(
                filename='success1.csv',
                total_rows=10,
                created_by='user',
                file_size_bytes=1024,
                file_hash='s1'
            )
            job1.status = JobStatus.COMPLETED
            job1.successful_rows = 10
            job1.failed_rows = 0
            job1.processed_rows = 10
            
            # Job completado con algunos errores
            job2 = BulkUploadJob(
                filename='success2.csv',
                total_rows=20,
                created_by='user',
                file_size_bytes=2048,
                file_hash='s2'
            )
            job2.status = JobStatus.COMPLETED
            job2.successful_rows = 18
            job2.failed_rows = 2
            job2.processed_rows = 20
            
            # Job fallido
            job3 = BulkUploadJob(
                filename='failed.csv',
                total_rows=5,
                created_by='user',
                file_size_bytes=512,
                file_hash='s3'
            )
            job3.status = JobStatus.FAILED
            
            # Job en progreso
            job4 = BulkUploadJob(
                filename='processing.csv',
                total_rows=15,
                created_by='user',
                file_size_bytes=1536,
                file_hash='s4'
            )
            job4.status = JobStatus.PROCESSING
            
            # Job cancelado
            job5 = BulkUploadJob(
                filename='cancelled.csv',
                total_rows=8,
                created_by='user',
                file_size_bytes=768,
                file_hash='s5'
            )
            job5.status = JobStatus.CANCELLED
            
            db.session.add_all([job1, job2, job3, job4, job5])
            db.session.commit()
        
        response = client.get('/api/products/bulk-upload/stats')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['total_jobs'] == 5
        assert data['completed'] == 2
        assert data['failed'] == 1
        assert data['in_progress'] == 1
        assert data['cancelled'] == 1
        assert data['total_products_imported'] == 28  # 10 + 18
        assert data['average_success_rate'] == 95.0  # (100 + 90) / 2
    
    def test_get_stats_average_calculation(self, client, app):
        """Debe calcular correctamente el promedio de success rate"""
        with app.app_context():
            from src.session import db
            
            # 100% success
            job1 = BulkUploadJob(
                filename='perfect.csv',
                total_rows=10,
                created_by='user',
                file_size_bytes=1024,
                file_hash='p1'
            )
            job1.status = JobStatus.COMPLETED
            job1.successful_rows = 10
            job1.failed_rows = 0
            job1.processed_rows = 10
            
            # 80% success
            job2 = BulkUploadJob(
                filename='partial.csv',
                total_rows=10,
                created_by='user',
                file_size_bytes=1024,
                file_hash='p2'
            )
            job2.status = JobStatus.COMPLETED
            job2.successful_rows = 8
            job2.failed_rows = 2
            job2.processed_rows = 10
            
            db.session.add_all([job1, job2])
            db.session.commit()
        
        response = client.get('/api/products/bulk-upload/stats')
        
        assert response.status_code == 200
        data = response.get_json()
        
        # (100 + 80) / 2 = 90
        assert data['average_success_rate'] == 90.0

