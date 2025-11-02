import json
from io import BytesIO


class TestVisitFilesBlueprint:
    """Test cases for visit files blueprint endpoints"""
    
    def test_upload_file_success(self, client, sample_visit):
        """Test POST /visits/<id>/files - upload file successfully."""
        # Create test file data
        test_data = b'This is test PDF content'
        
        data = {
            'file': (BytesIO(test_data), 'test_document.pdf', 'application/pdf')
        }
        
        response = client.post(f'/visits/{sample_visit.id}/files',
                              data=data,
                              content_type='multipart/form-data')
        
        assert response.status_code == 201
        response_data = json.loads(response.data)
        assert response_data['success'] is True
        assert 'message' in response_data
        assert 'file' in response_data
        
        file_data = response_data['file']
        assert file_data['visit_id'] == sample_visit.id
        assert file_data['file_name'] == 'test_document.pdf'
        assert file_data['mime_type'] == 'application/pdf'
        assert file_data['file_size'] == len(test_data)
    
    def test_upload_file_no_file_provided(self, client, sample_visit):
        """Test uploading without providing a file."""
        response = client.post(f'/visits/{sample_visit.id}/files',
                              data={},
                              content_type='multipart/form-data')
        
        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert response_data['success'] is False
        assert 'No se envió ningún archivo' in response_data['message']
    
    def test_upload_file_invalid_extension(self, client, sample_visit):
        """Test uploading file with invalid extension."""
        test_data = b'Invalid file content'
        
        data = {
            'file': (BytesIO(test_data), 'test.invalid', 'application/octet-stream')
        }
        
        response = client.post(f'/visits/{sample_visit.id}/files',
                              data=data,
                              content_type='multipart/form-data')
        
        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert response_data['success'] is False
        assert 'Extensión no permitida' in response_data['message']
    

    
    def test_upload_different_file_types(self, client, sample_visit):
        """Test uploading different allowed file types."""
        file_types = [
            ('document.pdf', 'application/pdf'),
            ('image.jpg', 'image/jpeg'),
            ('image.png', 'image/png'),
            ('spreadsheet.xlsx', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
            ('text.txt', 'text/plain'),
            ('compressed.zip', 'application/zip')
        ]
        
        for filename, mime_type in file_types:
            test_data = f'Test content for {filename}'.encode()
            
            data = {
                'file': (BytesIO(test_data), filename, mime_type)
            }
            
            response = client.post(f'/visits/{sample_visit.id}/files',
                                  data=data,
                                  content_type='multipart/form-data')
            
            assert response.status_code == 201, f"Failed for {filename}"
            response_data = json.loads(response.data)
            assert response_data['success'] is True
            assert response_data['file']['file_name'] == filename
            assert response_data['file']['mime_type'] == mime_type
    
    def test_list_visit_files(self, client, sample_visit, sample_visit_file):
        """Test GET /visits/<id>/files - list files for a visit."""
        response = client.get(f'/visits/{sample_visit.id}/files')
        
        assert response.status_code == 200
        files = json.loads(response.data)
        assert isinstance(files, list)
        assert len(files) >= 1
        
        # Check file structure
        file_data = files[0]
        assert 'id' in file_data
        assert 'visit_id' in file_data
        assert 'file_name' in file_data
        assert 'file_size' in file_data
        assert 'mime_type' in file_data
        assert 'uploaded_at' in file_data
        assert file_data['visit_id'] == sample_visit.id
    
    def test_list_visit_files_with_metadata(self, client, sample_visit, sample_visit_file):
        """Test GET /visits/<id>/files?include_metadata=true."""
        response = client.get(f'/visits/{sample_visit.id}/files?include_metadata=true')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, dict)
        assert 'visit_id' in data
        assert 'files' in data
        assert 'total_files' in data
        assert 'total_size' in data
        
        assert data['visit_id'] == sample_visit.id
        assert isinstance(data['files'], list)
        assert data['total_files'] == len(data['files'])
        assert data['total_size'] >= 0
    
    def test_list_visit_files_empty(self, client, sample_visit):
        """Test listing files for visit with no files."""
        response = client.get(f'/visits/{sample_visit.id}/files')
        
        assert response.status_code == 200
        files = json.loads(response.data)
        assert isinstance(files, list)
        # Could be empty or have files from other tests
    

    
    def test_download_file_not_found(self, client, sample_visit):
        """Test downloading non-existent file."""
        response = client.get(f'/visits/{sample_visit.id}/files/99999/download')
        
        assert response.status_code == 404
    
    def test_download_file_wrong_visit(self, client, sample_visit, sample_visit_file):
        """Test downloading file with wrong visit ID."""
        response = client.get(f'/visits/99999/files/{sample_visit_file.id}/download')
        
        assert response.status_code == 404
    
    def test_delete_file_by_visit_and_id(self, client, sample_visit):
        """Test DELETE /visits/<id>/files/<file_id> - delete file."""
        # First upload a file
        test_data = b'File to delete'
        data = {
            'file': (BytesIO(test_data), 'delete_test.pdf', 'application/pdf')
        }
        
        upload_response = client.post(f'/visits/{sample_visit.id}/files',
                                     data=data,
                                     content_type='multipart/form-data')
        
        assert upload_response.status_code == 201
        file_data = json.loads(upload_response.data)['file']
        file_id = file_data['id']
        
        # Now delete the file
        delete_response = client.delete(f'/visits/{sample_visit.id}/files/{file_id}')
        
        assert delete_response.status_code == 200
        response_data = json.loads(delete_response.data)
        assert response_data['success'] is True
        assert response_data['deleted_file_id'] == file_id
        
        # Verify file is deleted
        download_response = client.get(f'/visits/{sample_visit.id}/files/{file_id}/download')
        assert download_response.status_code == 404
    
    def test_delete_file_global(self, client, sample_visit):
        """Test DELETE /visits/files/<file_id> - global file deletion."""
        # First upload a file
        test_data = b'File to delete globally'
        data = {
            'file': (BytesIO(test_data), 'global_delete_test.pdf', 'application/pdf')
        }
        
        upload_response = client.post(f'/visits/{sample_visit.id}/files',
                                     data=data,
                                     content_type='multipart/form-data')
        
        assert upload_response.status_code == 201
        file_data = json.loads(upload_response.data)['file']
        file_id = file_data['id']
        
        # Now delete using global endpoint
        delete_response = client.delete(f'/visits/files/{file_id}')
        
        assert delete_response.status_code == 200
        response_data = json.loads(delete_response.data)
        assert response_data['success'] is True
        assert response_data['deleted_file_id'] == file_id
    
    def test_delete_file_not_found(self, client, sample_visit):
        """Test deleting non-existent file."""
        response = client.delete(f'/visits/{sample_visit.id}/files/99999')
        
        assert response.status_code == 404
    
    def test_get_file_stats(self, client, sample_visit, sample_visit_file):
        """Test GET /visits/<id>/files/stats - get file statistics."""
        response = client.get(f'/visits/{sample_visit.id}/files/stats')
        
        assert response.status_code == 200
        stats = json.loads(response.data)
        
        assert 'visit_id' in stats
        assert 'total_files' in stats
        assert 'total_size' in stats
        assert 'average_size' in stats
        assert 'file_types' in stats
        
        assert stats['visit_id'] == sample_visit.id
        assert stats['total_files'] >= 1
        assert stats['total_size'] >= 0
        assert isinstance(stats['file_types'], dict)
    
    def test_get_file_stats_no_files(self, client, sample_visit):
        """Test file stats for visit with no files."""
        response = client.get(f'/visits/{sample_visit.id}/files/stats')
        
        assert response.status_code == 200
        stats = json.loads(response.data)
        
        assert stats['visit_id'] == sample_visit.id
        # Stats should handle zero files gracefully
        assert stats['total_files'] >= 0
        assert stats['total_size'] >= 0
    
    def test_file_stats_with_multiple_types(self, client, sample_visit):
        """Test file statistics with multiple file types."""
        # Upload different file types
        files_to_upload = [
            ('doc1.pdf', b'PDF content 1', 'application/pdf'),
            ('doc2.pdf', b'PDF content 2 longer', 'application/pdf'),
            ('image.jpg', b'JPEG content', 'image/jpeg'),
            ('sheet.xlsx', b'Excel content here', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        ]
        
        for filename, content, mime_type in files_to_upload:
            data = {
                'file': (BytesIO(content), filename, mime_type)
            }
            
            response = client.post(f'/visits/{sample_visit.id}/files',
                                  data=data,
                                  content_type='multipart/form-data')
            assert response.status_code == 201
        
        # Get stats
        response = client.get(f'/visits/{sample_visit.id}/files/stats')
        assert response.status_code == 200
        stats = json.loads(response.data)
        
        assert stats['total_files'] >= 4
        assert len(stats['file_types']) >= 3  # At least 3 different types
        
        # Check specific file type stats
        file_types = stats['file_types']
        if 'application/pdf' in file_types:
            assert file_types['application/pdf']['count'] >= 2
    
    def test_file_operations_visit_not_found(self, client):
        """Test file operations on non-existent visit."""
        # List files
        response = client.get('/visits/99999/files')
        assert response.status_code == 404
        
        # File stats
        response = client.get('/visits/99999/files/stats')
        assert response.status_code == 404
    
    def test_file_name_sanitization(self, client, sample_visit):
        """Test that file names are properly handled."""
        # Test with special characters
        test_files = [
            'file with spaces.pdf',
            'file-with-dashes.pdf', 
            'file_with_underscores.pdf',
            'FILE_UPPERCASE.PDF',
            'file.with.dots.pdf'
        ]
        
        for filename in test_files:
            test_data = f'Content for {filename}'.encode()
            data = {
                'file': (BytesIO(test_data), filename, 'application/pdf')
            }
            
            response = client.post(f'/visits/{sample_visit.id}/files',
                                  data=data,
                                  content_type='multipart/form-data')
            
            assert response.status_code == 201, f"Failed for filename: {filename}"
            file_data = json.loads(response.data)['file']
            # Original filename should be preserved in database
            assert filename in file_data['file_name']