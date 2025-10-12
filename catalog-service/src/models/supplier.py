from src.session import db
from datetime import datetime

class Supplier(db.Model):
    __tablename__ = 'suppliers'
    
    # Primary Key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Información básica
    name = db.Column(db.String(255), nullable=False, index=True)
    legal_name = db.Column(db.String(255), nullable=False)
    tax_id = db.Column(db.String(50), unique=True, nullable=False)
    
    # Contacto
    email = db.Column(db.String(255))
    phone = db.Column(db.String(50))
    website = db.Column(db.String(255))
    
    # Dirección
    address_line1 = db.Column(db.String(255))
    address_line2 = db.Column(db.String(255))
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    country = db.Column(db.String(100), nullable=False)
    postal_code = db.Column(db.String(20))
    
    # Información comercial
    payment_terms = db.Column(db.String(100))  # ej: "Net 30", "Net 60"
    credit_limit = db.Column(db.Numeric(15, 2))
    currency = db.Column(db.String(3), default='USD')
    
    # Certificaciones
    is_certified = db.Column(db.Boolean, default=False)
    certification_date = db.Column(db.Date)
    certification_expiry = db.Column(db.Date)
    
    # Estado
    is_active = db.Column(db.Boolean, default=True, index=True)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relaciones
    products = db.relationship('Product', back_populates='supplier', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'legal_name': self.legal_name,
            'tax_id': self.tax_id,
            'email': self.email,
            'phone': self.phone,
            'website': self.website,
            'address': {
                'line1': self.address_line1,
                'line2': self.address_line2,
                'city': self.city,
                'state': self.state,
                'country': self.country,
                'postal_code': self.postal_code,
            },
            'payment_terms': self.payment_terms,
            'credit_limit': float(self.credit_limit) if self.credit_limit else None,
            'currency': self.currency,
            'is_certified': self.is_certified,
            'certification_date': self.certification_date.isoformat() if self.certification_date else None,
            'certification_expiry': self.certification_expiry.isoformat() if self.certification_expiry else None,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def __repr__(self):
        return f'<Supplier {self.name}>'
