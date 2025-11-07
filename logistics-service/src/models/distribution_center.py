from src.session import db
from datetime import datetime

class DistributionCenter(db.Model):
    __tablename__ = 'distribution_centers'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False, index=True)
    address = db.Column(db.String(500))
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100))
    country = db.Column(db.String(100), nullable=False)
    postal_code = db.Column(db.String(20))
    
    phone = db.Column(db.String(50))
    email = db.Column(db.String(255))
    manager_name = db.Column(db.String(255))
    
    capacity_m3 = db.Column(db.Numeric(10, 2))
    is_active = db.Column(db.Boolean, default=True, index=True)
    supports_cold_chain = db.Column(db.Boolean, default=False)
    
    # Coordenadas geográficas para el optimizador de rutas
    latitude = db.Column(db.Numeric(10, 7))
    longitude = db.Column(db.Numeric(10, 7))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    inventory_items = db.relationship('Inventory', back_populates='distribution_center', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'country': self.country,
            'postal_code': self.postal_code,
            'phone': self.phone,
            'email': self.email,
            'manager_name': self.manager_name,
            'capacity_m3': float(self.capacity_m3) if self.capacity_m3 else None,
            'is_active': self.is_active,
            'supports_cold_chain': self.supports_cold_chain,
            'latitude': float(self.latitude) if self.latitude else None,
            'longitude': float(self.longitude) if self.longitude else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def __repr__(self):
        return f'<DistributionCenter {self.code}: {self.name}>'
