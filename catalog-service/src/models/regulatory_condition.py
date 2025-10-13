from src.session import db
from datetime import datetime

class RegulatoryCondition(db.Model):
    __tablename__ = 'regulatory_conditions'
    
    # Primary Key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Relación con producto
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    
    # País y regulación
    country = db.Column(db.String(100), nullable=False, index=True)
    regulatory_body = db.Column(db.String(255))  # INVIMA, COFEPRIS, DIGEMID, etc.
    
    # Restricciones
    import_restrictions = db.Column(db.Text)
    special_handling_requirements = db.Column(db.Text)
    distribution_restrictions = db.Column(db.Text)
    
    # Documentación requerida
    required_documentation = db.Column(db.Text)
    
    # Estado
    is_approved_for_sale = db.Column(db.Boolean, default=False)
    approval_date = db.Column(db.Date)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relaciones
    product = db.relationship('Product', back_populates='regulatory_conditions')
    
    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'country': self.country,
            'regulatory_body': self.regulatory_body,
            'import_restrictions': self.import_restrictions,
            'special_handling_requirements': self.special_handling_requirements,
            'distribution_restrictions': self.distribution_restrictions,
            'required_documentation': self.required_documentation,
            'is_approved_for_sale': self.is_approved_for_sale,
            'approval_date': self.approval_date.isoformat() if self.approval_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
    
    def __repr__(self):
        return f'<RegulatoryCondition {self.country} - Product {self.product_id}>'
