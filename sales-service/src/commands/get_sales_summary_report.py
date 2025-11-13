"""
Command to get sales summary report with aggregated data.
Combines orders, order items, salespersons, and goals for comprehensive sales analysis.
"""
from typing import List, Dict, Any, Optional
from sqlalchemy import func, extract, text
from src.session import db
from src.models.order import Order
from src.models.order_item import OrderItem
from src.entities.salesperson import Salesperson
from src.entities.salesperson_goal import SalespersonGoal
from src.errors.errors import ValidationError


class GetSalesSummaryReport:
    """
    Command to generate sales summary report with aggregated metrics.
    
    Combines:
    - Order data (date, status)
    - Order items (products, quantities, values)
    - Salesperson information (name, region, territory)
    - Goals (targets for products and amounts)
    
    Supports filtering by:
    - Date range (from_date, to_date)
    - Region
    - Territory
    - Product SKU
    - Salesperson employee_id
    - Month/Year
    """
    
    def __init__(
        self,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        region: Optional[str] = None,
        territory: Optional[str] = None,
        product_sku: Optional[str] = None,
        employee_id: Optional[str] = None,
        month: Optional[int] = None,
        year: Optional[int] = None,
        order_status: Optional[str] = None
    ):
        self.from_date = from_date
        self.to_date = to_date
        self.region = region
        self.territory = territory
        self.product_sku = product_sku
        self.employee_id = employee_id
        self.month = month
        self.year = year
        self.order_status = order_status
        
    def execute(self) -> Dict[str, Any]:
        """
        Execute the sales summary report query.
        
        Returns:
            Dictionary with summary data and metadata
        """
        # Build base query with joins - AGRUPAR SOLO POR VENTAS REALES
        query = db.session.query(
            func.date(Order.order_date).label('fecha'),
            Salesperson.employee_id.label('employee_id'),
            func.concat(Salesperson.first_name, ' ', Salesperson.last_name).label('vendedor'),
            Salesperson.territory.label('territory'),
            OrderItem.product_sku.label('product_sku'),
            OrderItem.product_name.label('product_name'),
            func.sum(OrderItem.quantity).label('volumen_ventas'),
            func.sum(OrderItem.total).label('valor_total')
        ).select_from(Order)\
         .join(OrderItem, Order.id == OrderItem.order_id)\
         .join(Salesperson, Order.seller_id == Salesperson.employee_id)
        
        # Apply filters
        query = self._apply_filters(query)
        
        # Group by - SIN incluir campos de SalespersonGoal
        query = query.group_by(
            func.date(Order.order_date),
            Salesperson.employee_id,
            Salesperson.first_name,
            Salesperson.last_name,
            Salesperson.territory,
            OrderItem.product_sku,
            OrderItem.product_name
        )
        
        # Order by date and salesperson
        query = query.order_by(
            func.date(Order.order_date).desc(),
            Salesperson.employee_id
        )
        
        # Execute query
        results = query.all()
        
        # Format results and get goals for each row
        summary_data = []
        for row in results:
            # Buscar objetivos para este vendedor y producto
            goals = SalespersonGoal.query.filter_by(
                id_vendedor=row.employee_id,
                id_producto=row.product_sku
            ).all()
            
            # Extraer objetivos de unidades y monetarios
            goal_units = None
            goal_amount = None
            region = None
            
            for goal in goals:
                if goal.tipo == 'unidades':
                    goal_units = float(goal.valor_objetivo)
                    if not region:
                        region = goal.region
                elif goal.tipo == 'monetario':
                    goal_amount = float(goal.valor_objetivo)
                    if not region:
                        region = goal.region
            
            item = {
                'fecha': row.fecha.isoformat() if row.fecha else None,
                'employee_id': row.employee_id,
                'vendedor': row.vendedor,
                'region': region,  # Región del objetivo (si existe)
                'territory': row.territory,
                'product_sku': row.product_sku,
                'product_name': row.product_name,
                'volumen_ventas': int(row.volumen_ventas) if row.volumen_ventas else 0,
                'valor_total': float(row.valor_total) if row.valor_total else 0.0,
                'objetivo_unidades': goal_units,
                'objetivo_monetario': goal_amount,
            }
            
            # Calculate achievement percentages
            if goal_units and row.volumen_ventas:
                item['cumplimiento_unidades'] = round(
                    (float(row.volumen_ventas) / goal_units) * 100, 2
                )
            else:
                item['cumplimiento_unidades'] = None
                
            if goal_amount and row.valor_total:
                item['cumplimiento_monetario'] = round(
                    (float(row.valor_total) / goal_amount) * 100, 2
                )
            else:
                item['cumplimiento_monetario'] = None
            
            summary_data.append(item)
        
        # Calculate totals
        totals = self._calculate_totals(summary_data)
        
        return {
            'summary': summary_data,
            'totals': totals,
            'filters_applied': self._get_applied_filters(),
            'total_records': len(summary_data)
        }
    
    def _apply_filters(self, query):
        """Apply all filters to the query."""
        
        # Date range filter
        if self.from_date:
            try:
                query = query.filter(Order.order_date >= self.from_date)
            except Exception:
                raise ValidationError('Invalid from_date format. Use YYYY-MM-DD')
        
        if self.to_date:
            try:
                query = query.filter(Order.order_date <= self.to_date)
            except Exception:
                raise ValidationError('Invalid to_date format. Use YYYY-MM-DD')
        
        # Month/Year filter
        if self.month:
            if not 1 <= self.month <= 12:
                raise ValidationError('Month must be between 1 and 12')
            query = query.filter(extract('month', Order.order_date) == self.month)
        
        if self.year:
            if self.year < 2000 or self.year > 2100:
                raise ValidationError('Invalid year')
            query = query.filter(extract('year', Order.order_date) == self.year)
        
        # Region filter
        if self.region:
            query = query.filter(SalespersonGoal.region == self.region)
        
        # Territory filter
        if self.territory:
            query = query.filter(Salesperson.territory == self.territory)
        
        # Product SKU filter
        if self.product_sku:
            query = query.filter(OrderItem.product_sku == self.product_sku)
        
        # Employee ID filter
        if self.employee_id:
            query = query.filter(Salesperson.employee_id == self.employee_id)
        
        # Order status filter
        if self.order_status:
            query = query.filter(Order.status == self.order_status)
        
        return query
    
    def _calculate_totals(self, summary_data: List[Dict]) -> Dict[str, Any]:
        """Calculate total aggregates from summary data."""
        if not summary_data:
            return {
                'total_volumen_ventas': 0,
                'total_valor_total': 0.0,
                'unique_salespersons': 0,
                'unique_products': 0,
                'unique_regions': 0
            }
        
        total_volumen = sum(item['volumen_ventas'] for item in summary_data)
        total_valor = sum(item['valor_total'] for item in summary_data)
        unique_salespersons = len(set(item['employee_id'] for item in summary_data))
        unique_products = len(set(item['product_sku'] for item in summary_data))
        unique_regions = len(set(item['region'] for item in summary_data if item['region']))
        
        return {
            'total_volumen_ventas': total_volumen,
            'total_valor_total': round(total_valor, 2),
            'unique_salespersons': unique_salespersons,
            'unique_products': unique_products,
            'unique_regions': unique_regions
        }
    
    def _get_applied_filters(self) -> Dict[str, Any]:
        """Get dictionary of applied filters."""
        filters = {}
        
        if self.from_date:
            filters['from_date'] = self.from_date
        if self.to_date:
            filters['to_date'] = self.to_date
        if self.month:
            filters['month'] = self.month
        if self.year:
            filters['year'] = self.year
        if self.region:
            filters['region'] = self.region
        if self.territory:
            filters['territory'] = self.territory
        if self.product_sku:
            filters['product_sku'] = self.product_sku
        if self.employee_id:
            filters['employee_id'] = self.employee_id
        if self.order_status:
            filters['order_status'] = self.order_status
        
        return filters
