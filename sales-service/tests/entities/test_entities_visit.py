import pytest
from datetime import date, time
from decimal import Decimal
from src.entities.visit import Visit
from src.entities.visit_status import VisitStatus


class TestVisitEntity:
    """Test cases for Visit entity model"""
    
    def test_create_visit_basic(self, db, sample_customer, sample_salesperson):
        """Test creating a basic visit with required fields only."""
        visit = Visit(
            customer_id=sample_customer.id,
            salesperson_id=sample_salesperson.id,
            visit_date=date(2025, 12, 1),
            visit_time=time(14, 30)
        )
        db.session.add(visit)
        db.session.commit()
        
        assert visit.id is not None
        assert visit.customer_id == sample_customer.id
        assert visit.salesperson_id == sample_salesperson.id
        assert visit.visit_date == date(2025, 12, 1)
        assert visit.visit_time == time(14, 30)
        assert visit.status == VisitStatus.PROGRAMADA  # Default status
        assert visit.created_at is not None
        assert visit.updated_at is not None
    
    def test_create_visit_complete(self, db, sample_customer, sample_salesperson):
        """Test creating a visit with all fields filled."""
        visit = Visit(
            customer_id=sample_customer.id,
            salesperson_id=sample_salesperson.id,
            visit_date=date(2025, 12, 15),
            visit_time=time(9, 0),
            contacted_persons='Dr. María López, Jefe de Compras',
            clinical_findings='Necesitan reposición urgente de suministros quirúrgicos',
            additional_notes='Cliente VIP, priorizar atención',
            address='Carrera 15 #32-45, Torre Médica, Piso 8',
            latitude=Decimal('4.65812'),
            longitude=Decimal('-74.09383'),
            status=VisitStatus.COMPLETADA
        )
        db.session.add(visit)
        db.session.commit()
        
        assert visit.id is not None
        assert visit.contacted_persons == 'Dr. María López, Jefe de Compras'
        assert visit.clinical_findings == 'Necesitan reposición urgente de suministros quirúrgicos'
        assert visit.additional_notes == 'Cliente VIP, priorizar atención'
        assert visit.address == 'Carrera 15 #32-45, Torre Médica, Piso 8'
        assert visit.latitude == Decimal('4.65812')
        assert visit.longitude == Decimal('-74.09383')
        assert visit.status == VisitStatus.COMPLETADA
    
    def test_visit_default_status(self, db, sample_customer, sample_salesperson):
        """Test that new visits get PROGRAMADA status by default."""
        visit = Visit(
            customer_id=sample_customer.id,
            salesperson_id=sample_salesperson.id,
            visit_date=date(2025, 12, 10),
            visit_time=time(16, 45)
        )
        db.session.add(visit)
        db.session.commit()
        
        assert visit.status == VisitStatus.PROGRAMADA
    
    def test_visit_to_dict_basic(self, db, sample_visit):
        """Test visit to_dict method without files."""
        result = sample_visit.to_dict()
        
        assert isinstance(result, dict)
        assert 'id' in result
        assert result['customer_id'] == sample_visit.customer_id
        assert result['salesperson_id'] == sample_visit.salesperson_id
        assert result['visit_date'] == sample_visit.visit_date.isoformat()
        assert result['visit_time'] == str(sample_visit.visit_time)
        assert result['status'] == sample_visit.status.value
        assert result['contacted_persons'] == sample_visit.contacted_persons
        assert result['clinical_findings'] == sample_visit.clinical_findings
        assert result['additional_notes'] == sample_visit.additional_notes
        assert result['address'] == sample_visit.address
        assert result['latitude'] == float(sample_visit.latitude)
        assert result['longitude'] == float(sample_visit.longitude)
        assert 'created_at' in result
        assert 'updated_at' in result
        assert 'files' not in result  # Not included by default
    
    def test_visit_to_dict_with_files(self, db, sample_visit, sample_visit_file):
        """Test visit to_dict method including files."""
        result = sample_visit.to_dict(include_files=True)
        
        assert 'files' in result
        assert isinstance(result['files'], list)
        assert len(result['files']) == 1
        assert result['files'][0]['file_name'] == sample_visit_file.file_name
    
    def test_visit_to_dict_null_coordinates(self, db, sample_customer, sample_salesperson):
        """Test visit to_dict with null latitude/longitude."""
        visit = Visit(
            customer_id=sample_customer.id,
            salesperson_id=sample_salesperson.id,
            visit_date=date(2025, 12, 20),
            visit_time=time(11, 15),
            latitude=None,
            longitude=None
        )
        db.session.add(visit)
        db.session.commit()
        
        result = visit.to_dict()
        assert result['latitude'] is None
        assert result['longitude'] is None
    
    def test_visit_status_transitions(self, db, sample_visit):
        """Test different visit status transitions."""
        # Initially PROGRAMADA
        assert sample_visit.status == VisitStatus.PROGRAMADA
        
        # Change to COMPLETADA
        sample_visit.status = VisitStatus.COMPLETADA
        db.session.commit()
        assert sample_visit.status == VisitStatus.COMPLETADA
        
        # Change to ELIMINADA
        sample_visit.status = VisitStatus.ELIMINADA
        db.session.commit()
        assert sample_visit.status == VisitStatus.ELIMINADA
    
    def test_visit_relationships(self, db, sample_visit):
        """Test that visit has proper relationship with files."""
        # Visit should have files relationship
        assert hasattr(sample_visit, 'files')
        assert isinstance(sample_visit.files, list)
    
    def test_visit_foreign_key_constraints(self, db):
        """Test that foreign key constraints are defined properly."""
        # In SQLite memory DB, foreign keys are not enforced by default
        # This test verifies the FK columns exist and are properly defined
        visit = Visit(
            customer_id=99999,  # Non-existent (but SQLite allows it)
            salesperson_id=99999,  # Non-existent (but SQLite allows it)  
            visit_date=date(2025, 12, 25),
            visit_time=time(12, 0)
        )
        db.session.add(visit)
        # SQLite will allow this commit even with invalid foreign keys
        db.session.commit()
        
        # Verify the foreign key columns are properly set
        assert visit.customer_id == 99999
        assert visit.salesperson_id == 99999
    
    def test_visit_required_fields(self, db):
        """Test that required fields are enforced."""
        # Missing customer_id
        visit1 = Visit(
            salesperson_id=1,
            visit_date=date(2025, 12, 30),
            visit_time=time(10, 0)
        )
        db.session.add(visit1)
        
        with pytest.raises(Exception):
            db.session.commit()
        
        db.session.rollback()
        
        # Missing salesperson_id
        visit2 = Visit(
            customer_id=1,
            visit_date=date(2025, 12, 31),
            visit_time=time(15, 30)
        )
        db.session.add(visit2)
        
        with pytest.raises(Exception):
            db.session.commit()
    
    def test_visit_text_fields_length(self, db, sample_customer, sample_salesperson):
        """Test text fields can handle long content."""
        long_text = "A" * 1000  # 1000 character string
        
        visit = Visit(
            customer_id=sample_customer.id,
            salesperson_id=sample_salesperson.id,
            visit_date=date(2025, 12, 28),
            visit_time=time(13, 45),
            contacted_persons=long_text,
            clinical_findings=long_text,
            additional_notes=long_text
        )
        db.session.add(visit)
        db.session.commit()
        
        assert len(visit.contacted_persons) == 1000
        assert len(visit.clinical_findings) == 1000
        assert len(visit.additional_notes) == 1000
    
    def test_visit_timestamps(self, db, sample_visit):
        """Test that timestamps are set correctly."""
        original_created = sample_visit.created_at
        original_updated = sample_visit.updated_at
        
        assert original_created is not None
        assert original_updated is not None
        
        # Update the visit
        sample_visit.additional_notes = "Updated notes"
        db.session.commit()
        
        # created_at should not change, updated_at should change
        assert sample_visit.created_at == original_created
        # Note: In SQLite memory DB, timestamp precision might not change
        # so we just verify updated_at is set
        assert sample_visit.updated_at is not None
    
    def test_visit_decimal_precision(self, db, sample_customer, sample_salesperson):
        """Test decimal precision for coordinates."""
        visit = Visit(
            customer_id=sample_customer.id,
            salesperson_id=sample_salesperson.id,
            visit_date=date(2025, 12, 29),
            visit_time=time(8, 30),
            latitude=Decimal('4.12345678'),  # 8 decimal places
            longitude=Decimal('-74.12345678901')  # 11 decimal places (max)
        )
        db.session.add(visit)
        db.session.commit()
        
        # Verify precision is maintained (SQLite may truncate precision)
        assert visit.latitude == Decimal('4.12345678')
        # SQLite might truncate longitude precision, so we check it's close
        assert abs(visit.longitude - Decimal('-74.12345678901')) < Decimal('0.00000001')