from datetime import datetime, date
from sqlalchemy.orm import joinedload
from sqlalchemy import and_, or_, func
from typing import List, Tuple

from src.entities.visit import Visit
from src.entities.visit_status import VisitStatus
from src.entities.salesperson import Salesperson
from src.models.customer import Customer
from src.dtos.visit_filters_and_utils import VisitFilterRequest
from src.dtos.visit_response import VisitListResponse, VisitListResult
from src.session import db
from src.errors.errors import ValidationError


class GetVisits:
    """Command to get visits with advanced filtering, pagination and sorting."""
    
    def __init__(self, filters: VisitFilterRequest):
        self.filters = filters
    
    def execute(self) -> VisitListResult:
        """
        Execute the command to get filtered visits.
        
        Returns:
            VisitListResult: Paginated list of visits with metadata
            
        Raises:
            ValidationError: If filter validation fails
        """
        
        # Build the query with filters
        query = self._build_base_query()
        
        # Apply filters
        query = self._apply_filters(query)
        
        # Apply sorting
        query = self._apply_sorting(query)
        
        # Get total count before pagination
        total_count = query.count()
        
        # Apply pagination
        offset = (self.filters.page - 1) * self.filters.per_page
        paginated_query = query.offset(offset).limit(self.filters.per_page)
        
        # Execute query
        visits = paginated_query.all()
        
        # Convert to response DTOs
        visit_responses = [self._build_visit_list_response(visit) for visit in visits]
        
        # Calculate pagination metadata
        total_pages = (total_count + self.filters.per_page - 1) // self.filters.per_page
        
        return VisitListResult(
            visits=visit_responses,
            total=total_count,
            page=self.filters.page,
            per_page=self.filters.per_page,
            pages=total_pages
        )
    
    def _build_base_query(self):
        """Build the base query with necessary joins."""
        return db.session.query(Visit)\
            .join(Customer, Visit.customer_id == Customer.id)\
            .join(Salesperson, Visit.salesperson_id == Salesperson.id)\
            .options(
                joinedload(Visit.customer),
                joinedload(Visit.salesperson),
                joinedload(Visit.files)
            )
    
    def _apply_filters(self, query):
        """Apply all filters to the query."""
        
        # Filter by customer ID
        if self.filters.customer_id:
            query = query.filter(Visit.customer_id == self.filters.customer_id)
        
        # Filter by salesperson ID
        if self.filters.salesperson_id:
            query = query.filter(Visit.salesperson_id == self.filters.salesperson_id)
        
        # Filter by status
        if self.filters.status:
            query = query.filter(Visit.status == self.filters.status)
        
        # Filter by date range
        if self.filters.visit_date_from:
            query = query.filter(Visit.visit_date >= self.filters.visit_date_from)
        
        if self.filters.visit_date_to:
            query = query.filter(Visit.visit_date <= self.filters.visit_date_to)
        
        # Filter by customer name (partial search)
        if self.filters.customer_name:
            customer_filter = f"%{self.filters.customer_name}%"
            query = query.filter(
                or_(
                    Customer.business_name.ilike(customer_filter),
                    Customer.trade_name.ilike(customer_filter)
                )
            )
        
        # Filter by salesperson name (partial search)
        if self.filters.salesperson_name:
            salesperson_filter = f"%{self.filters.salesperson_name}%"
            query = query.filter(
                or_(
                    Salesperson.first_name.ilike(salesperson_filter),
                    Salesperson.last_name.ilike(salesperson_filter),
                    func.concat(Salesperson.first_name, ' ', Salesperson.last_name).ilike(salesperson_filter)
                )
            )
        
        # Filter by address (partial search)
        if self.filters.address:
            address_filter = f"%{self.filters.address}%"
            query = query.filter(Visit.address.ilike(address_filter))
        
        return query
    
    def _apply_sorting(self, query):
        """Apply sorting to the query."""
        
        sort_field = self.filters.sort_by or 'visit_date'
        sort_order = self.filters.sort_order or 'desc'
        
        # Define sorting mapping
        sort_mapping = {
            'visit_date': Visit.visit_date,
            'visit_time': Visit.visit_time,
            'created_at': Visit.created_at,
            'updated_at': Visit.updated_at,
            'customer_name': Customer.business_name,
            'salesperson_name': func.concat(Salesperson.first_name, ' ', Salesperson.last_name),
            'status': Visit.status
        }
        
        if sort_field in sort_mapping:
            sort_column = sort_mapping[sort_field]
            
            if sort_order == 'asc':
                query = query.order_by(sort_column.asc())
            else:
                query = query.order_by(sort_column.desc())
        
        # Secondary sort by ID for consistent ordering
        query = query.order_by(Visit.id.desc())
        
        return query
    
    def _build_visit_list_response(self, visit: Visit) -> VisitListResponse:
        """Build a visit list response DTO from visit entity."""
        
        return VisitListResponse(
            id=visit.id,
            customer_id=visit.customer_id,
            customer_name=visit.customer.business_name,
            salesperson_id=visit.salesperson_id,
            salesperson_name=visit.salesperson.get_full_name(),
            visit_date=visit.visit_date,
            visit_time=visit.visit_time,
            address=visit.address,
            status=visit.status,
            files_count=len(visit.files) if visit.files else 0,
            created_at=visit.created_at
        )
    
    def get_summary_stats(self) -> dict:
        """Get summary statistics for the current filter set."""
        
        # Build query without pagination for stats
        query = self._build_base_query()
        query = self._apply_filters(query)
        
        # Count by status
        stats = {
            'total': query.count(),
            'scheduled': query.filter(Visit.status == VisitStatus.SCHEDULED).count(),
            'completed': query.filter(Visit.status == VisitStatus.COMPLETED).count(),
            'cancelled': query.filter(Visit.status == VisitStatus.CANCELLED).count()
        }
        
        return stats