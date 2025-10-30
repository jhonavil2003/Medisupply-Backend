from datetime import datetime, date, time
from decimal import Decimal
from sqlalchemy.orm import joinedload
from sqlalchemy import and_

from src.entities.visit import Visit
from src.entities.visit_status import VisitStatus
from src.entities.salesperson import Salesperson
from src.models.customer import Customer
from src.dtos.update_visit_request import UpdateVisitRequest
from src.dtos.visit_response import VisitResponse
from src.dtos.basic_info_dtos import CustomerBasicInfo, SalespersonBasicInfo, VisitFileResponse
from src.session import db
from src.errors.errors import ValidationError, NotFoundError


class UpdateVisit:
    """Command to update an existing visit with validation."""
    
    def __init__(self, visit_id: int, update_data: UpdateVisitRequest):
        self.visit_id = visit_id
        self.update_data = update_data
    
    def execute(self) -> VisitResponse:
        """
        Execute the command to update a visit.
        
        Returns:
            VisitResponse: Updated visit with complete information
            
        Raises:
            ValidationError: If validation fails
            NotFoundError: If visit not found
        """
        
        # Validate that there are updates to apply
        if not self.update_data.has_updates():
            raise ValidationError("No updates provided")
        
        # Get existing visit
        visit = self._get_visit_with_relations()
        
        if not visit:
            raise NotFoundError(f"Visit with ID {self.visit_id} not found")
        
        # Validate business rules
        self._validate_update_permissions(visit)
        
        # Validate scheduling conflicts if date/time changed
        if self.update_data.visit_date or self.update_data.visit_time:
            self._validate_no_scheduling_conflicts(visit)
        
        # Apply updates
        self._apply_updates(visit)
        
        # Save changes
        db.session.commit()
        
        # Return updated visit
        return self._build_complete_visit_response(visit)
    
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
    
    def _validate_update_permissions(self, visit: Visit):
        """Validate business rules for updating visits."""
        
        # Can't update cancelled visits
        if visit.status == VisitStatus.CANCELLED:
            raise ValidationError("Cannot update cancelled visits")
        
        # If trying to change status, validate transitions
        if self.update_data.status:
            self._validate_status_transition(visit.status, self.update_data.status)
        
        # Validate completed visits can only update certain fields
        if visit.status == VisitStatus.COMPLETED:
            restricted_fields = ['visit_date', 'visit_time']
            for field in restricted_fields:
                if getattr(self.update_data, field) is not None:
                    raise ValidationError(f"Cannot update {field} for completed visits")
    
    def _validate_status_transition(self, current_status: VisitStatus, new_status: VisitStatus):
        """Validate that status transition is allowed."""
        
        # Define allowed transitions
        allowed_transitions = {
            VisitStatus.SCHEDULED: [VisitStatus.COMPLETED, VisitStatus.CANCELLED],
            VisitStatus.COMPLETED: [VisitStatus.SCHEDULED],  # Allow rescheduling completed visits
            VisitStatus.CANCELLED: [VisitStatus.SCHEDULED]   # Allow reactivating cancelled visits
        }
        
        if new_status not in allowed_transitions.get(current_status, []):
            raise ValidationError(
                f"Invalid status transition from {current_status.value} to {new_status.value}"
            )
    
    def _validate_no_scheduling_conflicts(self, visit: Visit):
        """Validate that there are no scheduling conflicts if date/time is being changed."""
        
        # Determine the new date and time
        new_date = self.update_data.visit_date or visit.visit_date
        new_time = self.update_data.visit_time or visit.visit_time
        
        # Only check if date or time is actually changing
        if new_date == visit.visit_date and new_time == visit.visit_time:
            return
        
        # Check for conflicts with other visits by the same salesperson
        conflicting_visit = Visit.query.filter(
            and_(
                Visit.id != self.visit_id,  # Exclude current visit
                Visit.salesperson_id == visit.salesperson_id,
                Visit.visit_date == new_date,
                Visit.visit_time == new_time,
                Visit.status != VisitStatus.CANCELLED
            )
        ).first()
        
        if conflicting_visit:
            raise ValidationError(
                f"Salesperson already has a visit scheduled at {new_date} {new_time}"
            )
    
    def _apply_updates(self, visit: Visit):
        """Apply the updates to the visit entity."""
        
        # Update simple fields
        if self.update_data.visit_date is not None:
            visit.visit_date = self.update_data.visit_date
        
        if self.update_data.visit_time is not None:
            visit.visit_time = self.update_data.visit_time
        
        if self.update_data.contacted_persons is not None:
            visit.contacted_persons = self.update_data.contacted_persons
        
        if self.update_data.clinical_findings is not None:
            visit.clinical_findings = self.update_data.clinical_findings
        
        if self.update_data.additional_notes is not None:
            visit.additional_notes = self.update_data.additional_notes
        
        if self.update_data.address is not None:
            visit.address = self.update_data.address
        
        if self.update_data.latitude is not None:
            visit.latitude = self.update_data.latitude
        
        if self.update_data.longitude is not None:
            visit.longitude = self.update_data.longitude
        
        if self.update_data.status is not None:
            visit.status = self.update_data.status
        
        # Update timestamp
        visit.updated_at = datetime.utcnow()
    
    def _build_complete_visit_response(self, visit: Visit) -> VisitResponse:
        """Build the complete visit response DTO with all related information."""
        
        # Build customer basic info
        customer_info = CustomerBasicInfo(
            id=visit.customer.id,
            business_name=visit.customer.business_name,
            contact_name=visit.customer.contact_name,
            contact_email=visit.customer.contact_email,
            contact_phone=visit.customer.contact_phone,
            document_number=visit.customer.document_number,
            city=visit.customer.city
        )
        
        # Build salesperson basic info
        salesperson_info = SalespersonBasicInfo(
            id=visit.salesperson.id,
            employee_id=visit.salesperson.employee_id,
            first_name=visit.salesperson.first_name,
            last_name=visit.salesperson.last_name,
            full_name=visit.salesperson.get_full_name(),
            email=visit.salesperson.email,
            territory=visit.salesperson.territory
        )
        
        # Build visit files info
        files_info = []
        if visit.files:
            for file_entity in visit.files:
                file_response = VisitFileResponse(
                    id=file_entity.id,
                    file_name=file_entity.file_name,
                    file_path=file_entity.file_path,
                    file_size=file_entity.file_size,
                    file_size_formatted=file_entity.get_file_size_formatted(),
                    mime_type=file_entity.mime_type,
                    uploaded_at=file_entity.uploaded_at,
                    is_image=file_entity.is_image(),
                    is_document=file_entity.is_document()
                )
                files_info.append(file_response)
        
        # Build complete visit response
        visit_response = VisitResponse(
            id=visit.id,
            customer=customer_info,
            salesperson=salesperson_info,
            visit_date=visit.visit_date,
            visit_time=visit.visit_time,
            contacted_persons=visit.contacted_persons,
            clinical_findings=visit.clinical_findings,
            additional_notes=visit.additional_notes,
            address=visit.address,
            latitude=visit.latitude,
            longitude=visit.longitude,
            status=visit.status,
            files=files_info,
            files_count=len(files_info),
            created_at=visit.created_at,
            updated_at=visit.updated_at
        )
        
        return visit_response
    
    def get_update_summary(self) -> dict:
        """Get summary of what will be updated."""
        
        updates = {}
        update_dict = self.update_data.to_dict(exclude_none=True)
        
        for field, value in update_dict.items():
            if field == 'status' and isinstance(value, VisitStatus):
                updates[field] = value.value
            elif isinstance(value, (date, time)):
                updates[field] = str(value)
            else:
                updates[field] = value
        
        return {
            'visit_id': self.visit_id,
            'updates': updates,
            'update_count': len(updates)
        }