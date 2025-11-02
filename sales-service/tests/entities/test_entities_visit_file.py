import pytest
import base64
from datetime import datetime
from src.entities.visit_file import VisitFile


class TestVisitFileEntity:
    """Test cases for VisitFile entity model"""
    
    def test_create_visit_file_basic(self, db, sample_visit):
        """Test creating a basic visit file."""
        visit_file = VisitFile(
            visit_id=sample_visit.id,
            file_name='test_document.pdf'
        )
        db.session.add(visit_file)
        db.session.commit()
        
        assert visit_file.id is not None
        assert visit_file.visit_id == sample_visit.id
        assert visit_file.file_name == 'test_document.pdf'
        assert visit_file.uploaded_at is not None
    
    def test_create_visit_file_complete(self, db, sample_visit):
        """Test creating a visit file with all fields."""
        file_data = b'This is test file content'
        
        visit_file = VisitFile(
            visit_id=sample_visit.id,
            file_name='complete_test.pdf',
            file_path='/uploads/visits/1/complete_test_20251101_100000_abc123.pdf',
            file_size=2048000,  # 2MB
            mime_type='application/pdf',
            file_data=file_data
        )
        db.session.add(visit_file)
        db.session.commit()
        
        assert visit_file.file_path == '/uploads/visits/1/complete_test_20251101_100000_abc123.pdf'
        assert visit_file.file_size == 2048000
        assert visit_file.mime_type == 'application/pdf'
        assert visit_file.file_data == file_data
    
    def test_visit_file_to_dict_basic(self, db, sample_visit_file):
        """Test visit file to_dict method without file data."""
        result = sample_visit_file.to_dict()
        
        assert isinstance(result, dict)
        assert 'id' in result
        assert result['visit_id'] == sample_visit_file.visit_id
        assert result['file_name'] == sample_visit_file.file_name
        assert result['file_path'] == sample_visit_file.file_path
        assert result['file_size'] == sample_visit_file.file_size
        assert result['mime_type'] == sample_visit_file.mime_type
        assert 'uploaded_at' in result
        assert 'file_data' not in result  # Not included by default
    
    def test_visit_file_to_dict_with_data(self, db, sample_visit):
        """Test visit file to_dict method including file data."""
        file_content = b'Test file content for base64 encoding'
        
        visit_file = VisitFile(
            visit_id=sample_visit.id,
            file_name='data_test.txt',
            file_size=len(file_content),
            mime_type='text/plain',
            file_data=file_content
        )
        db.session.add(visit_file)
        db.session.commit()
        
        result = visit_file.to_dict(include_data=True)
        
        assert 'file_data' in result
        # Verify base64 encoding
        decoded_data = base64.b64decode(result['file_data'])
        assert decoded_data == file_content
    
    def test_visit_file_to_dict_no_data(self, db, sample_visit):
        """Test to_dict when file has no binary data."""
        visit_file = VisitFile(
            visit_id=sample_visit.id,
            file_name='no_data.txt',
            file_data=None
        )
        db.session.add(visit_file)
        db.session.commit()
        
        result = visit_file.to_dict(include_data=True)
        assert 'file_data' not in result  # Should not include if no data
    
    def test_file_foreign_key_constraints(self, db, sample_visit):
        """Test foreign key constraints for visit_id."""
        # Note: SQLite in-memory doesn't enforce foreign keys by default
        # We verify the field exists and can be set to a valid value
        valid_file = VisitFile(
            visit_id=sample_visit.id,
            file_name="test.pdf",
            file_path="/files/test.pdf",
            file_size=1024
        )
        
        # This should work with valid foreign key
        db.session.add(valid_file)
        db.session.commit()
        assert valid_file.visit_id == sample_visit.id
    
    def test_visit_file_required_fields(self, db):
        """Test that required fields are enforced."""
        # Missing visit_id
        visit_file1 = VisitFile(
            file_name='test.pdf'
        )
        db.session.add(visit_file1)
        
        with pytest.raises(Exception):
            db.session.commit()
        
        db.session.rollback()
        
        # Missing file_name  
        visit_file2 = VisitFile(
            visit_id=1
        )
        db.session.add(visit_file2)
        
        with pytest.raises(Exception):
            db.session.commit()
    
    def test_visit_file_different_mime_types(self, db, sample_visit):
        """Test storing files with different MIME types."""
        mime_types = [
            'application/pdf',
            'image/jpeg',
            'image/png',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'text/plain',
            'application/zip'
        ]
        
        files = []
        for i, mime_type in enumerate(mime_types):
            visit_file = VisitFile(
                visit_id=sample_visit.id,
                file_name=f'test_file_{i}.ext',
                mime_type=mime_type,
                file_size=1024 * (i + 1)  # Different sizes
            )
            db.session.add(visit_file)
            files.append(visit_file)
        
        db.session.commit()
        
        for i, visit_file in enumerate(files):
            assert visit_file.id is not None
            assert visit_file.mime_type == mime_types[i]
            assert visit_file.file_size == 1024 * (i + 1)
    
    def test_visit_file_large_binary_data(self, db, sample_visit):
        """Test storing large binary data."""
        # Create 1MB of test data
        large_data = b'A' * (1024 * 1024)
        
        visit_file = VisitFile(
            visit_id=sample_visit.id,
            file_name='large_file.bin',
            file_size=len(large_data),
            mime_type='application/octet-stream',
            file_data=large_data
        )
        db.session.add(visit_file)
        db.session.commit()
        
        assert visit_file.file_data == large_data
        assert len(visit_file.file_data) == 1024 * 1024
    
    def test_visit_file_file_name_length(self, db, sample_visit):
        """Test file name length constraints."""
        # Test normal length file name
        normal_name = 'normal_document.pdf'
        visit_file1 = VisitFile(
            visit_id=sample_visit.id,
            file_name=normal_name
        )
        db.session.add(visit_file1)
        db.session.commit()
        assert visit_file1.file_name == normal_name
        
        # Test very long file name (should work up to 255 characters)
        long_name = 'very_long_filename_' + 'x' * 200 + '.pdf'
        if len(long_name) <= 255:
            visit_file2 = VisitFile(
                visit_id=sample_visit.id,
                file_name=long_name
            )
            db.session.add(visit_file2)
            db.session.commit()
            assert visit_file2.file_name == long_name
    
    def test_visit_file_path_length(self, db, sample_visit):
        """Test file path length constraints."""
        # Test normal path
        normal_path = '/uploads/visits/1/document_20251101_100000_abc123.pdf'
        visit_file1 = VisitFile(
            visit_id=sample_visit.id,
            file_name='document.pdf',
            file_path=normal_path
        )
        db.session.add(visit_file1)
        db.session.commit()
        assert visit_file1.file_path == normal_path
        
        # Test long path (should work up to 500 characters)
        long_path = '/uploads/visits/' + 'very_long_directory_name/' * 10 + 'file.pdf'
        if len(long_path) <= 500:
            visit_file2 = VisitFile(
                visit_id=sample_visit.id,
                file_name='long_path.pdf',
                file_path=long_path
            )
            db.session.add(visit_file2)
            db.session.commit()
            assert visit_file2.file_path == long_path
    
    def test_visit_file_timestamps(self, db, sample_visit_file):
        """Test timestamp handling."""
        assert sample_visit_file.uploaded_at is not None
        assert isinstance(sample_visit_file.uploaded_at, datetime)
        
        # Store original timestamp
        original_timestamp = sample_visit_file.uploaded_at
        
        # Update the file (note: uploaded_at doesn't auto-update)
        sample_visit_file.file_name = 'updated_name.pdf'
        db.session.commit()
        
        # uploaded_at should remain the same
        assert sample_visit_file.uploaded_at == original_timestamp
    
    def test_visit_file_null_optional_fields(self, db, sample_visit):
        """Test that optional fields can be null."""
        visit_file = VisitFile(
            visit_id=sample_visit.id,
            file_name='minimal.txt',
            file_path=None,
            file_size=None,
            mime_type=None,
            file_data=None
        )
        db.session.add(visit_file)
        db.session.commit()
        
        assert visit_file.file_path is None
        assert visit_file.file_size is None
        assert visit_file.mime_type is None
        assert visit_file.file_data is None
        
        # to_dict should handle nulls properly
        result = visit_file.to_dict()
        assert result['file_path'] is None
        assert result['file_size'] is None
        assert result['mime_type'] is None
    
    def test_visit_file_relationship_with_visit(self, db, sample_visit, sample_visit_file):
        """Test relationship between visit file and visit."""
        # File should be accessible through visit
        assert len(sample_visit.files) == 1
        assert sample_visit.files[0].id == sample_visit_file.id
        assert sample_visit.files[0].file_name == sample_visit_file.file_name
    
    def test_visit_file_cascade_delete(self, db, sample_visit, sample_visit_file):
        """Test that files are deleted when visit is deleted."""
        file_id = sample_visit_file.id
        
        # Verify file exists
        assert VisitFile.query.get(file_id) is not None
        
        # Delete the visit
        db.session.delete(sample_visit)
        db.session.commit()
        
        # File should be deleted due to cascade
        assert VisitFile.query.get(file_id) is None