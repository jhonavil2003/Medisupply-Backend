"""
Tests para el endpoint de registro de URLs de archivos S3
"""
import json
import pytest


class TestVisitFilesS3Url:
    """Test cases para registro de URLs de S3 en visit_files"""
    
    def test_register_s3_url_success(self, client, sample_visit):
        """Test POST /visits/<id>/files con JSON (URL de S3) - éxito"""
        data = {
            "file_url": "https://medisupply-videos.s3.us-east-1.amazonaws.com/videos/2025/11/23/abc123_video.mp4",
            "file_name": "video_visita_123.mp4",
            "file_size": 15728640,
            "mime_type": "video/mp4"
        }
        
        response = client.post(
            f'/visits/{sample_visit.id}/files',
            json=data,
            content_type='application/json'
        )
        
        assert response.status_code == 201
        response_data = json.loads(response.data)
        assert response_data['success'] is True
        assert 'URL de archivo registrada exitosamente' in response_data['message']
        assert 'file' in response_data
        
        file_data = response_data['file']
        assert file_data['visit_id'] == sample_visit.id
        assert file_data['file_name'] == 'video_visita_123.mp4'
        assert file_data['file_path'].startswith('https://')
        assert file_data['mime_type'] == 'video/mp4'
        assert file_data['file_size'] == 15728640
    
    def test_register_s3_url_missing_file_url(self, client, sample_visit):
        """Test sin file_url - debe fallar"""
        data = {
            "file_name": "video_test.mp4",
            "file_size": 1024000,
            "mime_type": "video/mp4"
        }
        
        response = client.post(
            f'/visits/{sample_visit.id}/files',
            json=data,
            content_type='application/json'
        )
        
        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert response_data['success'] is False
        assert 'file_url' in response_data['message']
    
    def test_register_s3_url_missing_file_name(self, client, sample_visit):
        """Test sin file_name - debe fallar"""
        data = {
            "file_url": "https://medisupply-videos.s3.us-east-1.amazonaws.com/videos/test.mp4",
            "file_size": 1024000,
            "mime_type": "video/mp4"
        }
        
        response = client.post(
            f'/visits/{sample_visit.id}/files',
            json=data,
            content_type='application/json'
        )
        
        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert response_data['success'] is False
        assert 'file_name' in response_data['message']
    
    def test_register_s3_url_invalid_https(self, client, sample_visit):
        """Test con URL HTTP (no HTTPS) - debe fallar"""
        data = {
            "file_url": "http://medisupply-videos.s3.us-east-1.amazonaws.com/videos/test.mp4",
            "file_name": "video_test.mp4",
            "file_size": 1024000,
            "mime_type": "video/mp4"
        }
        
        response = client.post(
            f'/visits/{sample_visit.id}/files',
            json=data,
            content_type='application/json'
        )
        
        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert response_data['success'] is False
        assert 'HTTPS' in response_data['message']
    
    def test_register_s3_url_invalid_extension(self, client, sample_visit):
        """Test con extensión no permitida - debe fallar"""
        data = {
            "file_url": "https://medisupply-videos.s3.us-east-1.amazonaws.com/videos/test.exe",
            "file_name": "malware.exe",
            "file_size": 1024000,
            "mime_type": "application/x-msdownload"
        }
        
        response = client.post(
            f'/visits/{sample_visit.id}/files',
            json=data,
            content_type='application/json'
        )
        
        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert response_data['success'] is False
        assert 'Extensión no permitida' in response_data['message']
    
    def test_register_s3_url_visit_not_found(self, client):
        """Test con visita inexistente - debe fallar"""
        data = {
            "file_url": "https://medisupply-videos.s3.us-east-1.amazonaws.com/videos/test.mp4",
            "file_name": "video_test.mp4",
            "file_size": 1024000,
            "mime_type": "video/mp4"
        }
        
        response = client.post(
            '/visits/99999/files',
            json=data,
            content_type='application/json'
        )
        
        assert response.status_code == 404
        response_data = json.loads(response.data)
        assert response_data['success'] is False
        assert 'no existe' in response_data['message']
    
    def test_register_multiple_video_formats(self, client, sample_visit):
        """Test registrando múltiples formatos de video"""
        video_formats = [
            ('video.mp4', 'video/mp4'),
            ('video.avi', 'video/x-msvideo'),
            ('video.mov', 'video/quicktime'),
            ('video.mkv', 'video/x-matroska')
        ]
        
        for filename, mime_type in video_formats:
            data = {
                "file_url": f"https://medisupply-videos.s3.us-east-1.amazonaws.com/videos/{filename}",
                "file_name": filename,
                "file_size": 1024000,
                "mime_type": mime_type
            }
            
            response = client.post(
                f'/visits/{sample_visit.id}/files',
                json=data,
                content_type='application/json'
            )
            
            assert response.status_code == 201, f"Failed for {filename}"
            response_data = json.loads(response.data)
            assert response_data['success'] is True
            assert response_data['file']['file_name'] == filename
            assert response_data['file']['mime_type'] == mime_type
    
    def test_register_s3_url_without_optional_fields(self, client, sample_visit):
        """Test sin campos opcionales (file_size, mime_type)"""
        data = {
            "file_url": "https://medisupply-videos.s3.us-east-1.amazonaws.com/videos/test.mp4",
            "file_name": "video_test.mp4"
        }
        
        response = client.post(
            f'/visits/{sample_visit.id}/files',
            json=data,
            content_type='application/json'
        )
        
        assert response.status_code == 201
        response_data = json.loads(response.data)
        assert response_data['success'] is True
        assert response_data['file']['file_size'] == 0
        assert response_data['file']['mime_type'] == 'application/octet-stream'
    
    def test_unsupported_content_type(self, client, sample_visit):
        """Test con Content-Type no soportado"""
        response = client.post(
            f'/visits/{sample_visit.id}/files',
            data='plain text data',
            content_type='text/plain'
        )
        
        assert response.status_code == 415
        response_data = json.loads(response.data)
        assert response_data['success'] is False
        assert 'Content-Type no soportado' in response_data['message']
    
    def test_backward_compatibility_multipart(self, client, sample_visit):
        """Test que multipart/form-data sigue funcionando (retrocompatibilidad)"""
        from io import BytesIO
        
        test_data = b'This is test PDF content'
        data = {
            'file': (BytesIO(test_data), 'test_document.pdf', 'application/pdf')
        }
        
        response = client.post(
            f'/visits/{sample_visit.id}/files',
            data=data,
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 201
        response_data = json.loads(response.data)
        assert response_data['success'] is True
        assert 'Archivo subido exitosamente' in response_data['message']
