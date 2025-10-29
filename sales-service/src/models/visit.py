from sqlalchemy import Column, Integer, String, DateTime, Date, Time, Enum, Text, ForeignKey, DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from session import Base
import enum


class VisitStatus(enum.Enum):
    SCHEDULED = "SCHEDULED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class Visit(Base):
    __tablename__ = 'visits'

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey('customers.id', ondelete='CASCADE'), nullable=False)
    salesperson_id = Column(Integer, ForeignKey('salespersons.id', ondelete='RESTRICT'), nullable=False)
    visit_date = Column(Date, nullable=False, index=True)
    visit_time = Column(Time, nullable=False)
    contacted_persons = Column(Text, nullable=True)
    clinical_findings = Column(Text, nullable=True)
    additional_notes = Column(Text, nullable=True)
    address = Column(String(500), nullable=True)
    latitude = Column(DECIMAL(10, 8), nullable=True)
    longitude = Column(DECIMAL(11, 8), nullable=True)
    status = Column(Enum(VisitStatus), nullable=False, default=VisitStatus.SCHEDULED, index=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relaciones
    customer = relationship("Customer", back_populates="visits")
    salesperson = relationship("Salesperson", back_populates="visits")
    visit_files = relationship("VisitFile", back_populates="visit", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Visit(id={self.id}, customer_id={self.customer_id}, visit_date={self.visit_date}, status={self.status.value})>"

    def to_dict(self, include_files=False, include_customer=False, include_salesperson=False):
        """Convierte el modelo a diccionario para serialización JSON"""
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
            result['files'] = [file.to_dict() for file in self.visit_files]
        
        if include_customer and self.customer:
            result['customer'] = {
                'id': self.customer.id,
                'business_name': self.customer.business_name,
                'document_number': self.customer.document_number,
                'city': self.customer.city
            }
            
        if include_salesperson and self.salesperson:
            result['salesperson'] = {
                'id': self.salesperson.id,
                'employee_id': self.salesperson.employee_id,
                'full_name': f"{self.salesperson.first_name} {self.salesperson.last_name}",
                'territory': self.salesperson.territory
            }
            
        return result

    @staticmethod
    def from_dict(data):
        """Crea una instancia de Visit desde un diccionario"""
        visit = Visit()
        visit.customer_id = data.get('customer_id')
        visit.salesperson_id = data.get('salesperson_id')
        visit.visit_date = data.get('visit_date')
        visit.visit_time = data.get('visit_time')
        visit.contacted_persons = data.get('contacted_persons')
        visit.clinical_findings = data.get('clinical_findings')
        visit.additional_notes = data.get('additional_notes')
        visit.address = data.get('address')
        visit.latitude = data.get('latitude')
        visit.longitude = data.get('longitude')
        
        # Manejo del status
        status_value = data.get('status')
        if status_value and isinstance(status_value, str):
            try:
                visit.status = VisitStatus(status_value)
            except ValueError:
                visit.status = VisitStatus.SCHEDULED  # Default fallback
        elif status_value:
            visit.status = status_value
            
        return visit