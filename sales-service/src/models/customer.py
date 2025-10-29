from datetime import datetime
from src.session import db


class Customer(db.Model):
    """Customer model representing a client in the system."""
    
    __tablename__ = 'customers'
    
    id = db.Column(db.Integer, primary_key=True)
    document_type = db.Column(db.String(10), nullable=False)  # NIT, CC, CE
    document_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    business_name = db.Column(db.String(200), nullable=False)
    trade_name = db.Column(db.String(200))
    customer_type = db.Column(db.String(50), nullable=False)  # hospital, clinica, farmacia, distribuidor
    contact_name = db.Column(db.String(100))
    contact_email = db.Column(db.String(100))
    contact_phone = db.Column(db.String(20))
    address = db.Column(db.String(200))
    city = db.Column(db.String(100))
    department = db.Column(db.String(100))
    country = db.Column(db.String(100), default='Colombia')
    credit_limit = db.Column(db.Numeric(15, 2), default=0.0)
    credit_days = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    orders = db.relationship('Order', back_populates='customer', lazy='dynamic')
    visits = db.relationship('Visit', back_populates='customer', lazy='dynamic')
    
    def __repr__(self):
        return f'<Customer {self.document_number}: {self.business_name}>'
    
    def to_dict(self):
        """Convert customer to dictionary."""
        return {
            'id': self.id,
            'document_type': self.document_type,
            'document_number': self.document_number,
            'business_name': self.business_name,
            'trade_name': self.trade_name,
            'customer_type': self.customer_type,
            'contact_name': self.contact_name,
            'contact_email': self.contact_email,
            'contact_phone': self.contact_phone,
            'address': self.address,
            'city': self.city,
            'department': self.department,
            'country': self.country,
            'credit_limit': float(self.credit_limit) if self.credit_limit else 0.0,
            'credit_days': self.credit_days,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
