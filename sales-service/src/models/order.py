from datetime import datetime
from src.session import db


class Order(db.Model):
    """Order model representing a sales order in the system."""
    
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    seller_id = db.Column(db.String(50), nullable=False)  # ID del vendedor desde sistema externo
    seller_name = db.Column(db.String(100))
    order_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    status = db.Column(db.String(50), default='pending', nullable=False)  # pending, confirmed, processing, shipped, delivered, cancelled
    subtotal = db.Column(db.Numeric(15, 2), nullable=False)
    discount_amount = db.Column(db.Numeric(15, 2), default=0.0)
    tax_amount = db.Column(db.Numeric(15, 2), default=0.0)
    total_amount = db.Column(db.Numeric(15, 2), nullable=False)
    payment_terms = db.Column(db.String(50))  # contado, credito_30, credito_60, credito_90
    payment_method = db.Column(db.String(50))  # transferencia, cheque, efectivo
    delivery_address = db.Column(db.String(200))
    delivery_city = db.Column(db.String(100))
    delivery_department = db.Column(db.String(100))
    delivery_date = db.Column(db.DateTime)  # Fecha estimada/programada de entrega
    preferred_distribution_center = db.Column(db.String(50))  # Centro de distribución preferido
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    customer = db.relationship('Customer', back_populates='orders')
    items = db.relationship('OrderItem', back_populates='order', lazy='dynamic', cascade='all, delete-orphan')
    commercial_conditions = db.relationship('CommercialCondition', back_populates='order', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Order {self.order_number}: {self.status}>'
    
    def to_dict(self, include_items=False, include_customer=False):
        """Convert order to dictionary."""
        result = {
            'id': self.id,
            'order_number': self.order_number,
            'customer_id': self.customer_id,
            'seller_id': self.seller_id,
            'seller_name': self.seller_name or '',
            'order_date': self.order_date.isoformat() if self.order_date else None,
            'status': self.status,
            'subtotal': float(self.subtotal) if self.subtotal else 0.0,
            'discount_amount': float(self.discount_amount) if self.discount_amount else 0.0,
            'tax_amount': float(self.tax_amount) if self.tax_amount else 0.0,
            'total_amount': float(self.total_amount) if self.total_amount else 0.0,
            'payment_terms': self.payment_terms or '',
            'payment_method': self.payment_method or '',
            'delivery_address': self.delivery_address or '',
            'delivery_city': self.delivery_city or '',
            'delivery_department': self.delivery_department or '',
            'delivery_date': self.delivery_date.isoformat() if self.delivery_date else None,
            'preferred_distribution_center': self.preferred_distribution_center or 'CEDIS-BOG',
            'notes': self.notes or '',
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_items:
            result['items'] = [item.to_dict() for item in self.items]
        
        if include_customer and self.customer:
            result['customer'] = self.customer.to_dict()
        
        return result
