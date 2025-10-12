from datetime import datetime
from src.session import db


class CommercialCondition(db.Model):
    """CommercialCondition model representing special conditions applied to an order."""
    
    __tablename__ = 'commercial_conditions'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    condition_type = db.Column(db.String(50), nullable=False)  # descuento_volumen, promocion, descuento_pronto_pago
    description = db.Column(db.String(200), nullable=False)
    discount_percentage = db.Column(db.Numeric(5, 2), default=0.0)
    discount_amount = db.Column(db.Numeric(15, 2), default=0.0)
    applies_to = db.Column(db.String(50))  # order, item, category
    reference_id = db.Column(db.String(50))  # SKU del producto o ID de categoría si aplica
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    order = db.relationship('Order', back_populates='commercial_conditions')
    
    def __repr__(self):
        return f'<CommercialCondition {self.condition_type}: {self.description}>'
    
    def to_dict(self):
        """Convert commercial condition to dictionary."""
        return {
            'id': self.id,
            'order_id': self.order_id,
            'condition_type': self.condition_type,
            'description': self.description,
            'discount_percentage': float(self.discount_percentage) if self.discount_percentage else 0.0,
            'discount_amount': float(self.discount_amount) if self.discount_amount else 0.0,
            'applies_to': self.applies_to,
            'reference_id': self.reference_id,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
