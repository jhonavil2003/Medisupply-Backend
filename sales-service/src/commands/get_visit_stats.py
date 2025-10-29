from datetime import datetime, date, timedelta
from sqlalchemy import func, and_, extract
from typing import Dict, Any

from src.entities.visit import Visit
from src.entities.visit_status import VisitStatus
from src.entities.salesperson import Salesperson
from src.entities.visit_file import VisitFile
from src.models.customer import Customer
from src.dtos.visit_filters_and_utils import VisitStatsResponse
from src.session import db


class GetVisitStats:
    """Command to get comprehensive visit statistics and metrics."""
    
    def __init__(self, customer_id: int = None, salesperson_id: int = None, 
                 date_from: date = None, date_to: date = None):
        self.customer_id = customer_id
        self.salesperson_id = salesperson_id
        self.date_from = date_from
        self.date_to = date_to
    
    def execute(self) -> VisitStatsResponse:
        """
        Execute the command to get visit statistics.
        
        Returns:
            VisitStatsResponse: Comprehensive statistics
        """
        
        # Build base query with filters
        base_query = self._build_filtered_query()
        
        # Get basic counts
        basic_stats = self._get_basic_stats(base_query)
        
        # Get time-based stats
        time_stats = self._get_time_based_stats()
        
        # Get file statistics
        file_stats = self._get_file_stats(base_query)
        
        # Combine all statistics
        return VisitStatsResponse(
            total_visits=basic_stats['total'],
            scheduled_visits=basic_stats['scheduled'],
            completed_visits=basic_stats['completed'],
            cancelled_visits=basic_stats['cancelled'],
            visits_today=time_stats['today'],
            visits_this_week=time_stats['this_week'],
            visits_this_month=time_stats['this_month'],
            avg_files_per_visit=file_stats['avg_files_per_visit']
        )
    
    def _build_filtered_query(self):
        """Build base query with applied filters."""
        
        query = db.session.query(Visit)
        
        # Apply customer filter
        if self.customer_id:
            query = query.filter(Visit.customer_id == self.customer_id)
        
        # Apply salesperson filter
        if self.salesperson_id:
            query = query.filter(Visit.salesperson_id == self.salesperson_id)
        
        # Apply date range filters
        if self.date_from:
            query = query.filter(Visit.visit_date >= self.date_from)
        
        if self.date_to:
            query = query.filter(Visit.visit_date <= self.date_to)
        
        return query
    
    def _get_basic_stats(self, base_query) -> Dict[str, int]:
        """Get basic visit counts by status."""
        
        total = base_query.count()
        
        scheduled = base_query.filter(Visit.status == VisitStatus.SCHEDULED).count()
        completed = base_query.filter(Visit.status == VisitStatus.COMPLETED).count()
        cancelled = base_query.filter(Visit.status == VisitStatus.CANCELLED).count()
        
        return {
            'total': total,
            'scheduled': scheduled,
            'completed': completed,
            'cancelled': cancelled
        }
    
    def _get_time_based_stats(self) -> Dict[str, int]:
        """Get time-based visit statistics."""
        
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        month_start = today.replace(day=1)
        
        # Base query for time stats (without custom date filters)
        base_query = db.session.query(Visit)
        
        if self.customer_id:
            base_query = base_query.filter(Visit.customer_id == self.customer_id)
        
        if self.salesperson_id:
            base_query = base_query.filter(Visit.salesperson_id == self.salesperson_id)
        
        # Count visits for different time periods
        visits_today = base_query.filter(Visit.visit_date == today).count()
        
        visits_this_week = base_query.filter(
            Visit.visit_date >= week_start
        ).count()
        
        visits_this_month = base_query.filter(
            Visit.visit_date >= month_start
        ).count()
        
        return {
            'today': visits_today,
            'this_week': visits_this_week,
            'this_month': visits_this_month
        }
    
    def _get_file_stats(self, base_query) -> Dict[str, float]:
        """Get file-related statistics."""
        
        # Get total visits count
        total_visits = base_query.count()
        
        if total_visits == 0:
            return {'avg_files_per_visit': 0.0}
        
        # Count total files for visits in the filtered set
        visit_ids_subquery = base_query.with_entities(Visit.id).subquery()
        
        total_files = db.session.query(func.count(VisitFile.id))\
            .filter(VisitFile.visit_id.in_(visit_ids_subquery))\
            .scalar() or 0
        
        avg_files_per_visit = round(total_files / total_visits, 2) if total_visits > 0 else 0.0
        
        return {
            'avg_files_per_visit': avg_files_per_visit
        }
    
    def get_detailed_stats(self) -> Dict[str, Any]:
        """Get detailed statistics including breakdowns by various dimensions."""
        
        base_query = self._build_filtered_query()
        
        # Basic stats
        basic_stats = self._get_basic_stats(base_query)
        time_stats = self._get_time_based_stats()
        file_stats = self._get_file_stats(base_query)
        
        # Additional detailed stats
        detailed_stats = {
            **basic_stats,
            **time_stats,
            **file_stats,
            
            # Status distribution percentage
            'status_distribution': self._get_status_distribution(basic_stats),
            
            # Monthly breakdown
            'monthly_breakdown': self._get_monthly_breakdown(base_query),
            
            # Top customers by visit count
            'top_customers': self._get_top_customers(base_query),
            
            # Top salespersons by visit count
            'top_salespersons': self._get_top_salespersons(base_query),
            
            # Visit completion rate
            'completion_rate': self._calculate_completion_rate(basic_stats)
        }
        
        return detailed_stats
    
    def _get_status_distribution(self, basic_stats: Dict[str, int]) -> Dict[str, float]:
        """Calculate percentage distribution of visit statuses."""
        
        total = basic_stats['total']
        if total == 0:
            return {'scheduled': 0.0, 'completed': 0.0, 'cancelled': 0.0}
        
        return {
            'scheduled': round((basic_stats['scheduled'] / total) * 100, 2),
            'completed': round((basic_stats['completed'] / total) * 100, 2),
            'cancelled': round((basic_stats['cancelled'] / total) * 100, 2)
        }
    
    def _get_monthly_breakdown(self, base_query) -> list:
        """Get visit count breakdown by month for the last 6 months."""
        
        monthly_stats = db.session.query(
            extract('year', Visit.visit_date).label('year'),
            extract('month', Visit.visit_date).label('month'),
            func.count(Visit.id).label('count')
        ).filter(
            Visit.id.in_(base_query.with_entities(Visit.id))
        ).group_by(
            extract('year', Visit.visit_date),
            extract('month', Visit.visit_date)
        ).order_by(
            extract('year', Visit.visit_date).desc(),
            extract('month', Visit.visit_date).desc()
        ).limit(6).all()
        
        return [
            {
                'year': int(stat.year),
                'month': int(stat.month),
                'count': stat.count
            }
            for stat in monthly_stats
        ]
    
    def _get_top_customers(self, base_query, limit: int = 5) -> list:
        """Get top customers by visit count."""
        
        top_customers = db.session.query(
            Customer.business_name,
            func.count(Visit.id).label('visit_count')
        ).join(
            Visit, Visit.customer_id == Customer.id
        ).filter(
            Visit.id.in_(base_query.with_entities(Visit.id))
        ).group_by(
            Customer.id, Customer.business_name
        ).order_by(
            func.count(Visit.id).desc()
        ).limit(limit).all()
        
        return [
            {
                'customer_name': customer.business_name,
                'visit_count': customer.visit_count
            }
            for customer in top_customers
        ]
    
    def _get_top_salespersons(self, base_query, limit: int = 5) -> list:
        """Get top salespersons by visit count."""
        
        top_salespersons = db.session.query(
            func.concat(Salesperson.first_name, ' ', Salesperson.last_name).label('full_name'),
            func.count(Visit.id).label('visit_count')
        ).join(
            Visit, Visit.salesperson_id == Salesperson.id
        ).filter(
            Visit.id.in_(base_query.with_entities(Visit.id))
        ).group_by(
            Salesperson.id, Salesperson.first_name, Salesperson.last_name
        ).order_by(
            func.count(Visit.id).desc()
        ).limit(limit).all()
        
        return [
            {
                'salesperson_name': sp.full_name,
                'visit_count': sp.visit_count
            }
            for sp in top_salespersons
        ]
    
    def _calculate_completion_rate(self, basic_stats: Dict[str, int]) -> float:
        """Calculate visit completion rate percentage."""
        
        completed = basic_stats['completed']
        total_actionable = basic_stats['scheduled'] + basic_stats['completed']
        
        if total_actionable == 0:
            return 0.0
        
        return round((completed / total_actionable) * 100, 2)