from src.session import db
from datetime import datetime

class Certification(db.Model):
    __tablename__ = 'certifications'
    
    # Primary Key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Relación con producto
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    
    # Información de la certificación
    certification_type = db.Column(db.String(100), nullable=False)  # FDA, CE, INVIMA, etc.
    certification_number = db.Column(db.String(100), nullable=False)
    issuing_authority = db.Column(db.String(255), nullable=False)
    country = db.Column(db.String(100), nullable=False)
    
    # Vigencia
    issue_date = db.Column(db.Date, nullable=False)
    expiry_date = db.Column(db.Date)
    is_valid = db.Column(db.Boolean, default=True)
    
    # Documentos
    certificate_url = db.Column(db.String(500))
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relaciones
    product = db.relationship('Product', back_populates='certifications')
    
    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'certification_type': self.certification_type,
            'certification_number': self.certification_number,
            'issuing_authority': self.issuing_authority,
            'country': self.country,
            'issue_date': self.issue_date.isoformat() if self.issue_date else None,
            'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
            'is_valid': self.is_valid,
            'certificate_url': self.certificate_url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
    
    def __repr__(self):
        return f'<Certification {self.certification_type}: {self.certification_number}>'
