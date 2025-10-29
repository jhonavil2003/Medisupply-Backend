from sqlalchemy.orm import joinedload

from src.entities.visit import Visit
from src.entities.visit_status import VisitStatus
from src.session import db
from src.errors.errors import ValidationError, NotFoundError


class DeleteVisit:
    """Command to delete a visit with business rule validation."""
    
    def __init__(self, visit_id: int, force_delete: bool = False):
        self.visit_id = visit_id
        self.force_delete = force_delete
    
    def execute(self) -> dict:
        """
        Execute the command to delete a visit.
        
        Returns:
            dict: Summary of the deleted visit
            
        Raises:
            ValidationError: If deletion is not allowed
            NotFoundError: If visit not found
        """
        
        # Get visit with related entities
        visit = self._get_visit_with_relations()
        
        if not visit:
            raise NotFoundError(f"Visit with ID {self.visit_id} not found")
        
        # Validate deletion permissions
        if not self.force_delete:
            self._validate_deletion_permissions(visit)
        
        # Create summary before deletion
        deletion_summary = self._create_deletion_summary(visit)
        
        # Delete the visit (cascade will handle related files)
        db.session.delete(visit)
        db.session.commit()
        
        return deletion_summary
    
    def _get_visit_with_relations(self) -> Visit:
        """Get visit with all related entities loaded."""
        
        return db.session.query(Visit)\
            .options(
                joinedload(Visit.customer),
                joinedload(Visit.salesperson),
                joinedload(Visit.files)
            )\
            .filter(Visit.id == self.visit_id)\
            .first()
    
    def _validate_deletion_permissions(self, visit: Visit):
        """Validate business rules for visit deletion."""
        
        # Can't delete completed visits (business rule)
        if visit.status == VisitStatus.COMPLETED:
            raise ValidationError(
                "Cannot delete completed visits. Completed visits contain important business data."
            )
        
        # Warn about visits with files
        if visit.files and len(visit.files) > 0:
            raise ValidationError(
                f"Cannot delete visit with {len(visit.files)} attached files. "
                "Remove files first or use force_delete=True."
            )
        
        # Additional validation: can't delete visits from the past
        from datetime import date
        if visit.visit_date < date.today():
            raise ValidationError(
                "Cannot delete past visits. Past visits are important for audit trail."
            )
    
    def _create_deletion_summary(self, visit: Visit) -> dict:
        """Create a summary of what will be deleted."""
        
        return {
            'deleted_visit': {
                'id': visit.id,
                'customer_name': visit.customer.business_name,
                'salesperson_name': visit.salesperson.get_full_name(),
                'visit_date': visit.visit_date.isoformat(),
                'visit_time': str(visit.visit_time),
                'status': visit.status.value,
                'had_files': len(visit.files) > 0 if visit.files else False,
                'files_deleted': len(visit.files) if visit.files else 0
            },
            'deletion_timestamp': db.func.now(),
            'force_delete_used': self.force_delete
        }
    
    def soft_delete(self) -> dict:
        """
        Perform a soft delete by changing status to CANCELLED.
        
        Returns:
            dict: Summary of the soft deletion
        """
        
        # Get visit
        visit = self._get_visit_with_relations()
        
        if not visit:
            raise NotFoundError(f"Visit with ID {self.visit_id} not found")
        
        # Can't soft delete already cancelled visits
        if visit.status == VisitStatus.CANCELLED:
            raise ValidationError("Visit is already cancelled")
        
        # Store original status
        original_status = visit.status
        
        # Change status to cancelled
        visit.status = VisitStatus.CANCELLED
        visit.updated_at = db.func.now()
        
        db.session.commit()
        
        return {
            'soft_deleted_visit': {
                'id': visit.id,
                'customer_name': visit.customer.business_name,
                'salesperson_name': visit.salesperson.get_full_name(),
                'visit_date': visit.visit_date.isoformat(),
                'visit_time': str(visit.visit_time),
                'original_status': original_status.value,
                'new_status': VisitStatus.CANCELLED.value
            },
            'deletion_type': 'soft_delete',
            'can_be_restored': True
        }
    
    def restore_cancelled_visit(self) -> dict:
        """
        Restore a cancelled visit back to scheduled status.
        
        Returns:
            dict: Summary of the restoration
        """
        
        # Get visit
        visit = self._get_visit_with_relations()
        
        if not visit:
            raise NotFoundError(f"Visit with ID {self.visit_id} not found")
        
        # Can only restore cancelled visits
        if visit.status != VisitStatus.CANCELLED:
            raise ValidationError("Can only restore cancelled visits")
        
        # Validate that the visit date is still in the future
        from datetime import date
        if visit.visit_date < date.today():
            raise ValidationError("Cannot restore visits scheduled in the past")
        
        # Restore to scheduled status
        visit.status = VisitStatus.SCHEDULED
        visit.updated_at = db.func.now()
        
        db.session.commit()
        
        return {
            'restored_visit': {
                'id': visit.id,
                'customer_name': visit.customer.business_name,
                'salesperson_name': visit.salesperson.get_full_name(),
                'visit_date': visit.visit_date.isoformat(),
                'visit_time': str(visit.visit_time),
                'status': VisitStatus.SCHEDULED.value
            },
            'restoration_timestamp': db.func.now()
        }