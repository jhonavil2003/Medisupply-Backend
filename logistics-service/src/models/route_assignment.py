from src.session import db
from datetime import datetime


class RouteAssignment(db.Model):
    """
    Modelo para representar la asignación de un pedido a una ruta específica.
    Vincula pedidos del sales-service con rutas y paradas.
    """
    __tablename__ = 'route_assignments'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Relaciones
    route_id = db.Column(db.Integer, db.ForeignKey('delivery_routes.id'), nullable=False)
    stop_id = db.Column(db.Integer, db.ForeignKey('route_stops.id'), nullable=False)
    
    # Información del pedido (desde sales-service)
    order_id = db.Column(db.Integer, nullable=False, index=True)  # ID del pedido en sales-service
    order_number = db.Column(db.String(50), nullable=False, index=True)
    
    # Validaciones y restricciones del pedido
    requires_cold_chain = db.Column(db.Boolean, default=False)
    total_weight_kg = db.Column(db.Numeric(10, 2), default=0.0)
    total_volume_m3 = db.Column(db.Numeric(10, 3), default=0.0)
    total_items_count = db.Column(db.Integer, default=0)
    
    # Prioridad del pedido
    clinical_priority = db.Column(db.Integer, default=3)  # 1=Crítico, 2=Alto, 3=Normal
    
    # Fechas
    assignment_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Reasignación (si aplica)
    was_reassigned = db.Column(db.Boolean, default=False)
    reassigned_from_route_id = db.Column(db.Integer, db.ForeignKey('delivery_routes.id'))
    reassigned_from_stop_id = db.Column(db.Integer)
    reassignment_date = db.Column(db.DateTime)
    reassignment_reason = db.Column(db.Text)
    reassigned_by = db.Column(db.String(100))
    
    # Estado de la asignación
    status = db.Column(
        db.String(50), 
        default='assigned', 
        nullable=False
    )  # assigned, in_transit, delivered, failed, cancelled
    
    # Información de entrega
    delivery_date = db.Column(db.DateTime)
    delivered_by = db.Column(db.String(100))
    
    # Información del cliente (copia desde order para referencia rápida)
    customer_name = db.Column(db.String(200))
    customer_type = db.Column(db.String(50))
    delivery_address = db.Column(db.String(500))
    
    # Auditoría
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = db.Column(db.String(100))
    
    # Relaciones
    route = db.relationship('DeliveryRoute', foreign_keys=[route_id], back_populates='assignments')
    stop = db.relationship('RouteStop', back_populates='assignments')
    reassigned_from_route = db.relationship('DeliveryRoute', foreign_keys=[reassigned_from_route_id])
    
    # Índices compuestos
    __table_args__ = (
        db.Index('idx_assignment_route', 'route_id', 'status'),
        db.Index('idx_assignment_stop', 'stop_id', 'status'),
        db.Index('idx_assignment_order', 'order_id', 'status'),
        db.UniqueConstraint('order_id', name='uix_order_assignment'),  # Un pedido solo puede estar en una ruta activa
    )
    
    @property
    def is_delivered(self):
        """Indica si el pedido fue entregado"""
        return self.status == 'delivered'
    
    @property
    def is_critical(self):
        """Indica si el pedido es crítico"""
        return self.clinical_priority == 1
    
    @property
    def needs_special_handling(self):
        """Indica si requiere manejo especial (cadena de frío)"""
        return self.requires_cold_chain
    
    def to_dict(self, include_route=False, include_stop=False):
        """Convierte la asignación a diccionario"""
        data = {
            'id': self.id,
            'route_id': self.route_id,
            'stop_id': self.stop_id,
            'order': {
                'id': self.order_id,
                'order_number': self.order_number,
                'clinical_priority': self.clinical_priority,
                'is_critical': self.is_critical,
            },
            'requirements': {
                'requires_cold_chain': self.requires_cold_chain,
                'needs_special_handling': self.needs_special_handling,
            },
            'dimensions': {
                'weight_kg': float(self.total_weight_kg) if self.total_weight_kg else 0.0,
                'volume_m3': float(self.total_volume_m3) if self.total_volume_m3 else 0.0,
                'items_count': self.total_items_count,
            },
            'customer': {
                'name': self.customer_name,
                'type': self.customer_type,
                'delivery_address': self.delivery_address,
            },
            'assignment_date': self.assignment_date.isoformat() if self.assignment_date else None,
            'reassignment': {
                'was_reassigned': self.was_reassigned,
                'from_route_id': self.reassigned_from_route_id,
                'from_stop_id': self.reassigned_from_stop_id,
                'date': self.reassignment_date.isoformat() if self.reassignment_date else None,
                'reason': self.reassignment_reason,
                'by': self.reassigned_by,
            } if self.was_reassigned else None,
            'status': self.status,
            'delivery': {
                'date': self.delivery_date.isoformat() if self.delivery_date else None,
                'delivered_by': self.delivered_by,
            } if self.is_delivered else None,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by,
        }
        
        if include_route and self.route:
            data['route'] = self.route.to_dict()
        
        if include_stop and self.stop:
            data['stop'] = self.stop.to_dict()
        
        return data
    
    def __repr__(self):
        return f'<RouteAssignment Order#{self.order_number} → Route#{self.route_id} Stop#{self.stop_id}>'
