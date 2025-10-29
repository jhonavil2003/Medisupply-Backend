from sqlalchemy import Column, Integer, String, DateTime, Enum, Text, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from session import Base
import enum


class VisitStatus(enum.Enum):
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Visit(Base):
    __tablename__ = 'visits'

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey('customers.id', ondelete='CASCADE'), nullable=False)
    salesperson_id = Column(Integer, nullable=False, index=True)
    visit_date = Column(DateTime, nullable=False, index=True)
    visit_time = Column(String(10), nullable=False)  # HH:MM format
    location_address = Column(Text, nullable=True)
    location_latitude = Column(Float, nullable=True)
    location_longitude = Column(Float, nullable=True)
    status = Column(Enum(VisitStatus), nullable=False, default=VisitStatus.SCHEDULED, index=True)
    purpose = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relaciones
    customer = relationship("Customer", back_populates="visits")
    visit_files = relationship("VisitFile", back_populates="visit", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Visit(id={self.id}, customer_id={self.customer_id}, visit_date={self.visit_date}, status={self.status.value})>"

    def to_dict(self, include_files=False):
        """Convierte el modelo a diccionario para serialización JSON"""
        result = {
            'id': self.id,
            'customer_id': self.customer_id,
            'salesperson_id': self.salesperson_id,
            'visit_date': self.visit_date.isoformat() if self.visit_date else None,
            'visit_time': self.visit_time,
            'location_address': self.location_address,
            'location_latitude': self.location_latitude,
            'location_longitude': self.location_longitude,
            'status': self.status.value if self.status else None,
            'purpose': self.purpose,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_files:
            result['files'] = [file.to_dict() for file in self.visit_files]
            
        return result

    @staticmethod
    def from_dict(data):
        """Crea una instancia de Visit desde un diccionario"""
        visit = Visit()
        visit.customer_id = data.get('customer_id')
        visit.salesperson_id = data.get('salesperson_id')
        visit.visit_date = data.get('visit_date')
        visit.visit_time = data.get('visit_time')
        visit.location_address = data.get('location_address')
        visit.location_latitude = data.get('location_latitude')
        visit.location_longitude = data.get('location_longitude')
        visit.purpose = data.get('purpose')
        visit.notes = data.get('notes')
        
        # Manejo del status
        status_value = data.get('status')
        if status_value and isinstance(status_value, str):
            visit.status = VisitStatus(status_value)
        elif status_value:
            visit.status = status_value
            
        return visit