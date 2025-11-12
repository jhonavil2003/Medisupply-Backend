"""
Tests de integración para bulk_upload_suppliers blueprint.
Cubre todos los endpoints de carga masiva de suppliers.
"""
import pytest
import io
from src.models.bulk_upload_supplier_job import BulkUploadSupplierJob, JobStatus
from src.models.supplier import Supplier
from src.session import db


class TestUploadSuppliersCSV:
    """Tests para POST /api/suppliers/bulk-upload"""
    
    def test_upload_valid_csv(self, client, app):
        """Verifica que acepta y procesa un CSV válido"""
        csv_content = b"tax_id,name,address_line1,phone,email,country\n123456789,Test Supplier,123 Main St,555-1234,test@test.com,Colombia\n"
        
        data = {
            'file': (io.BytesIO(csv_content), 'suppliers.csv')
        }
        
        response = client.post('/api/suppliers/bulk-upload', 
                             data=data,
                             content_type='multipart/form-data')
        
        assert response.status_code == 202
        json_data = response.get_json()
        assert 'job_id' in json_data
        assert json_data['total_rows'] == 1
        assert json_data['filename'] == 'suppliers.csv'
    
    def test_upload_without_file(self, client):
        """Verifica que rechaza requests sin archivo"""
        response = client.post('/api/suppliers/bulk-upload',
                             data={},
                             content_type='multipart/form-data')
        
        assert response.status_code == 400
        json_data = response.get_json()
        assert 'error' in json_data
    
    def test_upload_empty_filename(self, client):
        """Verifica que rechaza archivos sin nombre"""
        data = {
            'file': (io.BytesIO(b'content'), '')
        }
        
        response = client.post('/api/suppliers/bulk-upload',
                             data=data,
                             content_type='multipart/form-data')
        
        assert response.status_code == 400
    
    def test_upload_invalid_structure(self, client):
        """Verifica que rechaza CSV con estructura inválida"""
        # CSV sin columna requerida 'email'
        csv_content = b"tax_id,name,address_line1,phone,country\n123456789,Test,123 Main,555-1234,Colombia\n"
        
        data = {
            'file': (io.BytesIO(csv_content), 'invalid.csv')
        }
        
        response = client.post('/api/suppliers/bulk-upload',
                             data=data,
                             content_type='multipart/form-data')
        
        assert response.status_code == 400
        json_data = response.get_json()
        assert 'error' in json_data
        assert 'details' in json_data


class TestGetJobStatus:
    """Tests para GET /api/suppliers/bulk-upload/jobs/<job_id>"""
    
    def test_get_existing_job(self, client, app):
        """Verifica que obtiene el estado de un job existente"""
        with app.app_context():
            job = BulkUploadSupplierJob(filename='test.csv', total_rows=10)
            db.session.add(job)
            db.session.commit()
            job_id = job.job_id
        
        response = client.get(f'/api/suppliers/bulk-upload/jobs/{job_id}')
        
        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data['job_id'] == job_id
        assert json_data['filename'] == 'test.csv'
        assert json_data['status'] == JobStatus.PENDING
    
    def test_get_nonexistent_job(self, client):
        """Verifica que retorna 404 para job inexistente"""
        response = client.get('/api/suppliers/bulk-upload/jobs/nonexistent-id')
        
        assert response.status_code == 404


class TestDownloadErrors:
    """Tests para GET /api/suppliers/bulk-upload/jobs/<job_id>/errors"""
    
    def test_download_errors_csv(self, client, app):
        """Verifica que descarga CSV con errores"""
        with app.app_context():
            job = BulkUploadSupplierJob(filename='test.csv', total_rows=2)
            job.add_error(2, {'tax_id': '123', 'name': 'Test'}, 'Error de validación')
            db.session.add(job)
            db.session.commit()
            job_id = job.job_id
        
        response = client.get(f'/api/suppliers/bulk-upload/jobs/{job_id}/errors')
        
        assert response.status_code == 200
        assert response.content_type == 'text/csv; charset=utf-8'
        assert b'row_number' in response.data
        assert b'error_message' in response.data
    
    def test_download_errors_no_errors(self, client, app):
        """Verifica que retorna 404 cuando no hay errores"""
        with app.app_context():
            job = BulkUploadSupplierJob(filename='test.csv', total_rows=1)
            db.session.add(job)
            db.session.commit()
            job_id = job.job_id
        
        response = client.get(f'/api/suppliers/bulk-upload/jobs/{job_id}/errors')
        
        assert response.status_code == 404
    
    def test_download_errors_nonexistent_job(self, client):
        """Verifica que retorna 404 para job inexistente"""
        response = client.get('/api/suppliers/bulk-upload/jobs/nonexistent/errors')
        
        assert response.status_code == 404


class TestGetUploadHistory:
    """Tests para GET /api/suppliers/bulk-upload/jobs"""
    
    def test_get_history_default_pagination(self, client, app):
        """Verifica que obtiene historial con paginación por defecto"""
        with app.app_context():
            # Crear varios jobs
            for i in range(15):
                job = BulkUploadSupplierJob(filename=f'test{i}.csv', total_rows=10)
                db.session.add(job)
            db.session.commit()
        
        response = client.get('/api/suppliers/bulk-upload/jobs')
        
        assert response.status_code == 200
        json_data = response.get_json()
        assert 'jobs' in json_data
        assert 'pagination' in json_data
        assert len(json_data['jobs']) == 10  # Default per_page
        assert json_data['pagination']['page'] == 1
    
    def test_get_history_custom_pagination(self, client, app):
        """Verifica paginación personalizada"""
        with app.app_context():
            for i in range(10):
                job = BulkUploadSupplierJob(filename=f'test{i}.csv', total_rows=10)
                db.session.add(job)
            db.session.commit()
        
        response = client.get('/api/suppliers/bulk-upload/jobs?page=1&per_page=5')
        
        assert response.status_code == 200
        json_data = response.get_json()
        assert len(json_data['jobs']) == 5
        assert json_data['pagination']['per_page'] == 5
    
    def test_get_history_filter_by_status(self, client, app):
        """Verifica filtrado por estado"""
        with app.app_context():
            # Crear jobs con diferentes estados
            job1 = BulkUploadSupplierJob(filename='pending.csv', total_rows=10)
            job2 = BulkUploadSupplierJob(filename='completed.csv', total_rows=10)
            job2.set_status(JobStatus.COMPLETED)
            db.session.add_all([job1, job2])
            db.session.commit()
        
        response = client.get('/api/suppliers/bulk-upload/jobs?status=completed')
        
        assert response.status_code == 200
        json_data = response.get_json()
        for job in json_data['jobs']:
            assert job['status'] == JobStatus.COMPLETED
    
    def test_get_history_invalid_page(self, client):
        """Verifica que rechaza página inválida"""
        response = client.get('/api/suppliers/bulk-upload/jobs?page=0')
        
        assert response.status_code == 400
    
    def test_get_history_invalid_per_page(self, client):
        """Verifica que rechaza per_page inválido"""
        response = client.get('/api/suppliers/bulk-upload/jobs?per_page=200')
        
        assert response.status_code == 400


class TestGetUploadStats:
    """Tests para GET /api/suppliers/bulk-upload/stats"""
    
    def test_get_stats(self, client, app):
        """Verifica que obtiene estadísticas correctas"""
        with app.app_context():
            # Crear jobs con diferentes estados
            job1 = BulkUploadSupplierJob(filename='completed1.csv', total_rows=10)
            job1.set_status(JobStatus.COMPLETED)
            job1.successful_rows = 8
            job1.failed_rows = 2
            
            job2 = BulkUploadSupplierJob(filename='completed2.csv', total_rows=5)
            job2.set_status(JobStatus.COMPLETED)
            job2.successful_rows = 5
            job2.failed_rows = 0
            
            job3 = BulkUploadSupplierJob(filename='failed.csv', total_rows=10)
            job3.set_status(JobStatus.FAILED)
            
            db.session.add_all([job1, job2, job3])
            db.session.commit()
        
        response = client.get('/api/suppliers/bulk-upload/stats')
        
        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data['total_jobs'] == 3
        assert json_data['jobs_by_status']['completed'] == 2
        assert json_data['jobs_by_status']['failed'] == 1
        assert json_data['total_suppliers_created'] == 13  # 8 + 5
        assert json_data['total_rows_failed'] == 2


class TestCancelJob:
    """Tests para POST /api/suppliers/bulk-upload/jobs/<job_id>/cancel"""
    
    def test_cancel_pending_job(self, client, app):
        """Verifica que cancela un job en estado PENDING"""
        with app.app_context():
            job = BulkUploadSupplierJob(filename='test.csv', total_rows=10)
            db.session.add(job)
            db.session.commit()
            job_id = job.job_id
        
        response = client.post(f'/api/suppliers/bulk-upload/jobs/{job_id}/cancel')
        
        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data['status'] == JobStatus.CANCELLED
        
        # Verificar que el job fue actualizado
        with app.app_context():
            job = BulkUploadSupplierJob.query.filter_by(job_id=job_id).first()
            assert job.status == JobStatus.CANCELLED
    
    def test_cancel_processing_job(self, client, app):
        """Verifica que cancela un job en estado PROCESSING"""
        with app.app_context():
            job = BulkUploadSupplierJob(filename='test.csv', total_rows=10)
            job.set_status(JobStatus.PROCESSING)
            db.session.add(job)
            db.session.commit()
            job_id = job.job_id
        
        response = client.post(f'/api/suppliers/bulk-upload/jobs/{job_id}/cancel')
        
        assert response.status_code == 200
    
    def test_cancel_completed_job(self, client, app):
        """Verifica que no permite cancelar job completado"""
        with app.app_context():
            job = BulkUploadSupplierJob(filename='test.csv', total_rows=10)
            job.set_status(JobStatus.COMPLETED)
            db.session.add(job)
            db.session.commit()
            job_id = job.job_id
        
        response = client.post(f'/api/suppliers/bulk-upload/jobs/{job_id}/cancel')
        
        assert response.status_code == 400
    
    def test_cancel_nonexistent_job(self, client):
        """Verifica que retorna 404 para job inexistente"""
        response = client.post('/api/suppliers/bulk-upload/jobs/nonexistent/cancel')
        
        assert response.status_code == 404


class TestDownloadTemplate:
    """Tests para GET /api/suppliers/bulk-upload/template"""
    
    def test_download_template(self, client):
        """Verifica que descarga plantilla CSV con ejemplos"""
        response = client.get('/api/suppliers/bulk-upload/template')
        
        assert response.status_code == 200
        assert response.content_type == 'text/csv; charset=utf-8'
        assert b'tax_id' in response.data
        assert b'name' in response.data
        assert b'email' in response.data
        assert b'country' in response.data
        
        # Verificar que tiene ejemplos (al menos 3 filas de datos + header)
        lines = response.data.decode('utf-8').split('\n')
        assert len(lines) >= 4  # header + 3 ejemplos + posible línea vacía
    
    def test_template_has_all_columns(self, client):
        """Verifica que la plantilla tiene todas las columnas requeridas y opcionales"""
        response = client.get('/api/suppliers/bulk-upload/template')
        
        content = response.data.decode('utf-8')
        
        # Columnas requeridas
        assert 'tax_id' in content
        assert 'name' in content
        assert 'address_line1' in content
        assert 'phone' in content
        assert 'email' in content
        assert 'country' in content
        
        # Columnas opcionales
        assert 'legal_name' in content
        assert 'website' in content
        assert 'currency' in content
        assert 'is_certified' in content
        assert 'certification_date' in content
