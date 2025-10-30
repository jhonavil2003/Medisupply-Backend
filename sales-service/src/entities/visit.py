from src.session import db
from src.entities.visit_status import VisitStatus


class Visit(db.Model):
    """Entidad Visit - Representa una visita a cliente en el sistema"""
    
    __tablename__ = 'visits'

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    salesperson_id = db.Column(db.Integer, db.ForeignKey('salespersons.id'), nullable=False)
    visit_date = db.Column(db.Date, nullable=False)
    visit_time = db.Column(db.Time, nullable=False)
    contacted_persons = db.Column(db.Text)
    clinical_findings = db.Column(db.Text)
    additional_notes = db.Column(db.Text)
    address = db.Column(db.String(500))
    latitude = db.Column(db.DECIMAL(10, 8))
    longitude = db.Column(db.DECIMAL(11, 8))
    status = db.Column(db.Enum(VisitStatus, name='visit_status'), nullable=False, default=VisitStatus.SCHEDULED)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    # Relationships
    files = db.relationship("VisitFile", backref="visit", cascade="all, delete-orphan", lazy="select")

    def to_dict(self, include_files=False):
        result = {
            'id': self.id,
            'customer_id': self.customer_id,
            'salesperson_id': self.salesperson_id,
            'visit_date': self.visit_date.isoformat() if self.visit_date else None,
            'visit_time': str(self.visit_time) if self.visit_time else None,
            'contacted_persons': self.contacted_persons,
            'clinical_findings': self.clinical_findings,
            'additional_notes': self.additional_notes,
            'address': self.address,
            'latitude': float(self.latitude) if self.latitude else None,
            'longitude': float(self.longitude) if self.longitude else None,
            'status': self.status.value if self.status else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_files:
            result['files'] = [file.to_dict() for file in self.files]
            
        return result