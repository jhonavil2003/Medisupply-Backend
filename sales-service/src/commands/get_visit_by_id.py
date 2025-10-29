from sqlalchemy.orm import joinedload

from src.entities.visit import Visit
from src.entities.salesperson import Salesperson
from src.models.customer import Customer
from src.dtos.visit_response import VisitResponse
from src.dtos.basic_info_dtos import CustomerBasicInfo, SalespersonBasicInfo, VisitFileResponse
from src.session import db
from src.errors.errors import NotFoundError


class GetVisitById:
    """Command to get a specific visit by ID with complete information."""
    
    def __init__(self, visit_id: int):
        self.visit_id = visit_id
    
    def execute(self) -> VisitResponse:
        """
        Execute the command to get a visit by ID.
        
        Returns:
            VisitResponse: Complete visit information
            
        Raises:
            NotFoundError: If visit not found
        """
        
        # Get visit with all related data
        visit = self._get_visit_with_relations()
        
        # Validate visit exists
        if not visit:
            raise NotFoundError(f"Visit with ID {self.visit_id} not found")
        
        # Build complete response
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
    
    def get_visit_summary(self) -> dict:
        """Get a summary of the visit for quick reference."""
        
        visit = self._get_visit_with_relations()
        
        if not visit:
            raise NotFoundError(f"Visit with ID {self.visit_id} not found")
        
        return {
            'id': visit.id,
            'customer_name': visit.customer.business_name,
            'salesperson_name': visit.salesperson.get_full_name(),
            'visit_date': visit.visit_date.isoformat(),
            'visit_time': str(visit.visit_time),
            'status': visit.status.value,
            'has_files': len(visit.files) > 0 if visit.files else False,
            'files_count': len(visit.files) if visit.files else 0
        }