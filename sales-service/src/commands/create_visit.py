from datetime import datetime, date, time
from decimal import Decimal
from sqlalchemy.orm import sessionmaker
from sqlalchemy import and_

from src.entities.visit import Visit
from src.entities.visit_status import VisitStatus
from src.entities.salesperson import Salesperson
from src.models.customer import Customer
from src.dtos.create_visit_request import CreateVisitRequest
from src.dtos.visit_response import VisitResponse
from src.dtos.basic_info_dtos import CustomerBasicInfo, SalespersonBasicInfo
from src.session import db
from src.errors.errors import ValidationError, NotFoundError


class CreateVisit:
    """Command to create a new visit with validation of customer and salesperson."""
    
    def __init__(self, visit_data: CreateVisitRequest):
        self.visit_data = visit_data
    
    def execute(self) -> VisitResponse:
        """
        Execute the command to create a visit.
        
        Returns:
            VisitResponse: Created visit with complete information
            
        Raises:
            ValidationError: If validation fails
            NotFoundError: If customer or salesperson not found
        """
        
        # Validate customer exists
        customer = self._validate_customer()
        
        # Validate salesperson exists and is active
        salesperson = self._validate_salesperson()
        
        # Check for scheduling conflicts
        self._validate_no_scheduling_conflicts()
        
        # Create the visit entity
        visit = self._create_visit_entity()
        
        # Save to database
        db.session.add(visit)
        db.session.commit()
        
        # Return complete response
        return self._build_visit_response(visit, customer, salesperson)
    
    def _validate_customer(self) -> Customer:
        """Validate that customer exists and is active."""
        customer = Customer.query.filter_by(
            id=self.visit_data.customer_id
        ).first()
        
        if not customer:
            raise NotFoundError(f"Customer with ID {self.visit_data.customer_id} not found")
        
        if not customer.is_active:
            raise ValidationError(f"Customer {customer.business_name} is not active")
        
        return customer
    
    def _validate_salesperson(self) -> Salesperson:
        """Validate that salesperson exists and is active."""
        salesperson = Salesperson.query.filter_by(
            id=self.visit_data.salesperson_id
        ).first()
        
        if not salesperson:
            raise NotFoundError(f"Salesperson with ID {self.visit_data.salesperson_id} not found")
        
        if not salesperson.is_active:
            raise ValidationError(f"Salesperson {salesperson.get_full_name()} is not active")
        
        return salesperson
    
    def _validate_no_scheduling_conflicts(self):
        """Validate that there are no scheduling conflicts for the same salesperson."""
        # Check for visits at the same date and time for the same salesperson
        existing_visit = Visit.query.filter(
            and_(
                Visit.salesperson_id == self.visit_data.salesperson_id,
                Visit.visit_date == self.visit_data.visit_date,
                Visit.visit_time == self.visit_data.visit_time,
                Visit.status != VisitStatus.CANCELLED
            )
        ).first()
        
        if existing_visit:
            raise ValidationError(
                f"Salesperson already has a visit scheduled at "
                f"{self.visit_data.visit_date} {self.visit_data.visit_time}"
            )
        
        # Optional: Check for visits too close in time (within 1 hour)
        # This could be enhanced based on business requirements
    
    def _create_visit_entity(self) -> Visit:
        """Create the visit entity from validated data."""
        visit = Visit(
            customer_id=self.visit_data.customer_id,
            salesperson_id=self.visit_data.salesperson_id,
            visit_date=self.visit_data.visit_date,
            visit_time=self.visit_data.visit_time,
            contacted_persons=self.visit_data.contacted_persons,
            clinical_findings=self.visit_data.clinical_findings,
            additional_notes=self.visit_data.additional_notes,
            address=self.visit_data.address,
            latitude=self.visit_data.latitude,
            longitude=self.visit_data.longitude,
            status=VisitStatus.SCHEDULED
        )
        
        return visit
    
    def _build_visit_response(self, visit: Visit, customer: Customer, salesperson: Salesperson) -> VisitResponse:
        """Build the complete visit response DTO."""
        
        # Build customer basic info
        customer_info = CustomerBasicInfo(
            id=customer.id,
            business_name=customer.business_name,
            contact_name=customer.contact_name,
            contact_email=customer.contact_email,
            contact_phone=customer.contact_phone,
            document_number=customer.document_number,
            city=customer.city
        )
        
        # Build salesperson basic info
        salesperson_info = SalespersonBasicInfo(
            id=salesperson.id,
            employee_id=salesperson.employee_id,
            first_name=salesperson.first_name,
            last_name=salesperson.last_name,
            full_name=salesperson.get_full_name(),
            email=salesperson.email,
            territory=salesperson.territory
        )
        
        # Build visit response
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
            files=[],  # New visit has no files initially
            files_count=0,
            created_at=visit.created_at,
            updated_at=visit.updated_at
        )
        
        return visit_response