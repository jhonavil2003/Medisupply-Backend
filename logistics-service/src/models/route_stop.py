from src.session import db
from datetime import datetime, time
from decimal import Decimal


class RouteStop(db.Model):
    """
    Modelo para representar una parada individual en una ruta de entrega.
    Incluye información de ubicación, tiempos y prioridad.
    """
    __tablename__ = 'route_stops'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Relación con la ruta
    route_id = db.Column(db.Integer, db.ForeignKey('delivery_routes.id'), nullable=False)
    
    # Orden secuencial en la ruta
    sequence_order = db.Column(db.Integer, nullable=False)  # 1, 2, 3, 4, ...
    
    # Tipo de parada
    stop_type = db.Column(db.String(20), nullable=False)  # depot (origen), delivery, return
    
    # Cliente/Ubicación
    customer_id = db.Column(db.Integer)  # Relación conceptual con sales-service
    customer_name = db.Column(db.String(200))
    customer_type = db.Column(db.String(50))  # hospital, clinica, farmacia, distribuidor
    delivery_address = db.Column(db.String(500))
    
    # Coordenadas geográficas
    latitude = db.Column(db.Numeric(10, 7), nullable=False)
    longitude = db.Column(db.Numeric(10, 7), nullable=False)
    city = db.Column(db.String(100))
    department = db.Column(db.String(100))
    
    # Restricciones temporales (ventanas de entrega)
    time_window_start = db.Column(db.Time)  # Hora inicio ventana
    time_window_end = db.Column(db.Time)  # Hora fin ventana
    
    # Tiempos estimados
    estimated_arrival_time = db.Column(db.DateTime)
    estimated_service_time_minutes = db.Column(db.Integer, default=15)  # Tiempo de descarga/carga
    
    # Tiempos reales
    actual_arrival_time = db.Column(db.DateTime)
    actual_departure_time = db.Column(db.DateTime)
    actual_service_time_minutes = db.Column(db.Integer)
    
    # Distancia y tiempo desde la parada anterior
    distance_from_previous_km = db.Column(db.Numeric(10, 2), default=0.0)
    time_from_previous_minutes = db.Column(db.Integer, default=0)
    
    # Prioridad clínica
    clinical_priority = db.Column(db.Integer, default=3)  # 1=Crítico, 2=Alto, 3=Normal
    
    # Estado de la parada
    status = db.Column(
        db.String(50), 
        default='pending', 
        nullable=False
    )  # pending, arrived, in_service, completed, failed, skipped
    
    # Información de contacto
    contact_name = db.Column(db.String(100))
    contact_phone = db.Column(db.String(20))
    
    # Instrucciones especiales
    delivery_instructions = db.Column(db.Text)
    requires_signature = db.Column(db.Boolean, default=True)
    requires_cold_chain = db.Column(db.Boolean, default=False)
    
    # Información de entrega (cuando se completa)
    delivered_by = db.Column(db.String(100))
    received_by = db.Column(db.String(100))
    signature_image_url = db.Column(db.String(500))
    delivery_photo_url = db.Column(db.String(500))
    
    # Problemas o incidencias
    has_issues = db.Column(db.Boolean, default=False)
    issue_description = db.Column(db.Text)
    
    # Auditoría
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relaciones
    route = db.relationship('DeliveryRoute', back_populates='stops')
    assignments = db.relationship('RouteAssignment', back_populates='stop', lazy='dynamic', cascade='all, delete-orphan')
    
    # Índices compuestos
    __table_args__ = (
        db.Index('idx_route_sequence', 'route_id', 'sequence_order'),
        db.Index('idx_stop_status', 'route_id', 'status'),
        db.UniqueConstraint('route_id', 'sequence_order', name='uix_route_sequence'),
    )
    
    @property
    def is_depot(self):
        """Indica si la parada es el depósito/centro de distribución"""
        return self.stop_type == 'depot'
    
    @property
    def is_delivery(self):
        """Indica si la parada es una entrega"""
        return self.stop_type == 'delivery'
    
    @property
    def is_completed(self):
        """Indica si la parada está completada"""
        return self.status == 'completed'
    
    @property
    def is_critical(self):
        """Indica si la parada es crítica (prioridad 1)"""
        return self.clinical_priority == 1
    
    @property
    def is_within_time_window(self):
        """Verifica si la hora estimada de llegada está dentro de la ventana"""
        if not self.estimated_arrival_time or not self.time_window_start or not self.time_window_end:
            return True  # Si no hay ventana definida, asumimos que está bien
        
        arrival_time = self.estimated_arrival_time.time()
        return self.time_window_start <= arrival_time <= self.time_window_end
    
    @property
    def order_count(self):
        """Cuenta cuántos pedidos se entregan en esta parada"""
        return self.assignments.count()
    
    def to_dict(self, include_assignments=False):
        """Convierte la parada a diccionario"""
        data = {
            'id': self.id,
            'route_id': self.route_id,
            'sequence_order': self.sequence_order,
            'stop_type': self.stop_type,
            'is_depot': self.is_depot,
            'is_delivery': self.is_delivery,
            'customer': {
                'id': self.customer_id,
                'name': self.customer_name,
                'type': self.customer_type,
                'clinical_priority': self.clinical_priority,
                'is_critical': self.is_critical,
            } if self.customer_id else None,
            'location': {
                'address': self.delivery_address,
                'latitude': float(self.latitude) if self.latitude else None,
                'longitude': float(self.longitude) if self.longitude else None,
                'city': self.city,
                'department': self.department,
            },
            'time_window': {
                'start': self.time_window_start.isoformat() if self.time_window_start else None,
                'end': self.time_window_end.isoformat() if self.time_window_end else None,
                'is_within_window': self.is_within_time_window,
            },
            'estimated_times': {
                'arrival': self.estimated_arrival_time.isoformat() if self.estimated_arrival_time else None,
                'service_minutes': self.estimated_service_time_minutes,
            },
            'actual_times': {
                'arrival': self.actual_arrival_time.isoformat() if self.actual_arrival_time else None,
                'departure': self.actual_departure_time.isoformat() if self.actual_departure_time else None,
                'service_minutes': self.actual_service_time_minutes,
            },
            'from_previous': {
                'distance_km': float(self.distance_from_previous_km) if self.distance_from_previous_km else 0.0,
                'time_minutes': self.time_from_previous_minutes,
            },
            'status': self.status,
            'contact': {
                'name': self.contact_name,
                'phone': self.contact_phone,
            },
            'requirements': {
                'requires_signature': self.requires_signature,
                'requires_cold_chain': self.requires_cold_chain,
            },
            'delivery_instructions': self.delivery_instructions,
            'delivery_info': {
                'delivered_by': self.delivered_by,
                'received_by': self.received_by,
                'signature_url': self.signature_image_url,
                'photo_url': self.delivery_photo_url,
            } if self.is_completed else None,
            'issues': {
                'has_issues': self.has_issues,
                'description': self.issue_description,
            } if self.has_issues else None,
            'order_count': self.order_count,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if include_assignments:
            data['assignments'] = [assignment.to_dict() for assignment in self.assignments]
        
        return data
    
    def __repr__(self):
        return f'<RouteStop #{self.sequence_order} {self.stop_type} - {self.customer_name or "Depot"}>'
