from src.session import db
from datetime import datetime


class DeliveryRoute(db.Model):
    """
    Modelo para representar una ruta de entrega generada.
    Contiene información de la ruta optimizada, vehículo asignado y métricas.
    """
    __tablename__ = 'delivery_routes'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Identificación de la ruta
    route_code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    
    # Vehículo asignado
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.id'), nullable=False)
    driver_name = db.Column(db.String(100))
    driver_phone = db.Column(db.String(20))
    
    # Fechas de planificación
    generation_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    planned_date = db.Column(db.Date, nullable=False, index=True)
    
    # Estado de la ruta
    status = db.Column(
        db.String(50), 
        default='draft', 
        nullable=False,
        index=True
    )  # draft, active, in_progress, completed, cancelled
    
    # Métricas calculadas de la ruta
    total_distance_km = db.Column(db.Numeric(10, 2), default=0.0)
    estimated_duration_minutes = db.Column(db.Integer, default=0)
    total_orders = db.Column(db.Integer, default=0)
    total_stops = db.Column(db.Integer, default=0)
    total_weight_kg = db.Column(db.Numeric(10, 2), default=0.0)
    total_volume_m3 = db.Column(db.Numeric(10, 3), default=0.0)
    
    # Optimización
    optimization_score = db.Column(db.Numeric(5, 2))  # Score de calidad de ruta (0-100)
    optimization_strategy = db.Column(db.String(50))  # balanced, fastest, cheapest, priority_first
    has_cold_chain_products = db.Column(db.Boolean, default=False)
    
    # Centro de distribución origen
    distribution_center_id = db.Column(
        db.Integer, 
        db.ForeignKey('distribution_centers.id'), 
        nullable=False
    )
    
    # Tiempos estimados y reales
    estimated_start_time = db.Column(db.DateTime)
    actual_start_time = db.Column(db.DateTime)
    estimated_end_time = db.Column(db.DateTime)
    actual_end_time = db.Column(db.DateTime)
    
    # Costos
    estimated_cost = db.Column(db.Numeric(12, 2))  # Costo estimado de la ruta
    actual_cost = db.Column(db.Numeric(12, 2))  # Costo real (si se completa)
    
    # Información adicional
    notes = db.Column(db.Text)
    polyline = db.Column(db.Text)  # Encoded polyline de Google Maps para visualización
    
    # Auditoría
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = db.Column(db.String(100))
    
    # Relaciones
    vehicle = db.relationship('Vehicle', back_populates='delivery_routes')
    distribution_center = db.relationship('DistributionCenter', backref='delivery_routes')
    stops = db.relationship('RouteStop', back_populates='route', lazy='dynamic', cascade='all, delete-orphan')
    assignments = db.relationship(
        'RouteAssignment', 
        foreign_keys='RouteAssignment.route_id',
        back_populates='route', 
        lazy='dynamic', 
        cascade='all, delete-orphan'
    )
    
    # Índices compuestos
    __table_args__ = (
        db.Index('idx_route_planned_date', 'distribution_center_id', 'planned_date', 'status'),
        db.Index('idx_route_vehicle', 'vehicle_id', 'status'),
    )
    
    @property
    def is_completed(self):
        """Indica si la ruta está completada"""
        return self.status == 'completed'
    
    @property
    def is_active(self):
        """Indica si la ruta está activa o en progreso"""
        return self.status in ['active', 'in_progress']
    
    @property
    def completion_percentage(self):
        """Calcula el porcentaje de completitud basado en paradas completadas"""
        if self.total_stops == 0:
            return 0
        completed_stops = self.stops.filter_by(status='completed').count()
        return (completed_stops / self.total_stops) * 100
    
    @property
    def actual_duration_minutes(self):
        """Calcula la duración real si la ruta está en progreso o completada"""
        if self.actual_start_time and self.actual_end_time:
            delta = self.actual_end_time - self.actual_start_time
            return int(delta.total_seconds() / 60)
        elif self.actual_start_time:
            delta = datetime.utcnow() - self.actual_start_time
            return int(delta.total_seconds() / 60)
        return None
    
    def to_dict(self, include_stops=False, include_vehicle=False, include_assignments=False):
        """Convierte la ruta a diccionario"""
        data = {
            'id': self.id,
            'route_code': self.route_code,
            'vehicle_id': self.vehicle_id,
            'driver': {
                'name': self.driver_name,
                'phone': self.driver_phone,
            },
            'dates': {
                'generation_date': self.generation_date.isoformat() if self.generation_date else None,
                'planned_date': self.planned_date.isoformat() if self.planned_date else None,
            },
            'status': self.status,
            'metrics': {
                'total_distance_km': float(self.total_distance_km) if self.total_distance_km else 0.0,
                'estimated_duration_minutes': self.estimated_duration_minutes,
                'actual_duration_minutes': self.actual_duration_minutes,
                'total_orders': self.total_orders,
                'total_stops': self.total_stops,
                'total_weight_kg': float(self.total_weight_kg) if self.total_weight_kg else 0.0,
                'total_volume_m3': float(self.total_volume_m3) if self.total_volume_m3 else 0.0,
                'completion_percentage': self.completion_percentage,
            },
            'optimization': {
                'score': float(self.optimization_score) if self.optimization_score else None,
                'strategy': self.optimization_strategy,
                'has_cold_chain_products': self.has_cold_chain_products,
            },
            'distribution_center_id': self.distribution_center_id,
            'times': {
                'estimated_start': self.estimated_start_time.isoformat() if self.estimated_start_time else None,
                'actual_start': self.actual_start_time.isoformat() if self.actual_start_time else None,
                'estimated_end': self.estimated_end_time.isoformat() if self.estimated_end_time else None,
                'actual_end': self.actual_end_time.isoformat() if self.actual_end_time else None,
            },
            'costs': {
                'estimated': float(self.estimated_cost) if self.estimated_cost else None,
                'actual': float(self.actual_cost) if self.actual_cost else None,
            },
            'notes': self.notes,
            'polyline': self.polyline,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by,
        }
        
        if include_vehicle and self.vehicle:
            data['vehicle'] = self.vehicle.to_dict()
        
        if include_stops:
            data['stops'] = [stop.to_dict() for stop in self.stops.order_by('sequence_order')]
        
        if include_assignments:
            data['assignments'] = [assignment.to_dict() for assignment in self.assignments]
        
        return data
    
    def __repr__(self):
        return f'<DeliveryRoute {self.route_code} ({self.status})>'
