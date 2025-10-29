from sqlalchemy import Column, Integer, String, Date, Time, DateTime, Text, ForeignKey, DECIMAL, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.session import Base
from src.entities.visit_status import VisitStatus
from datetime import datetime, date, time
from decimal import Decimal
from typing import List, Optional


class Visit(Base):
    """Entidad Visit - Representa una visita a cliente en el sistema"""
    
    __tablename__ = 'visits'

    # Primary Key
    id: int = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign Keys
    customer_id: int = Column(Integer, ForeignKey('customers.id'), nullable=False)
    salesperson_id: int = Column(Integer, ForeignKey('salespersons.id'), nullable=False)
    
    # Visit Information
    visit_date: date = Column(Date, nullable=False, index=True)
    visit_time: time = Column(Time, nullable=False)
    contacted_persons: Optional[str] = Column(Text, nullable=True)
    clinical_findings: Optional[str] = Column(Text, nullable=True)
    additional_notes: Optional[str] = Column(Text, nullable=True)
    
    # Location Information
    address: Optional[str] = Column(String(500), nullable=True)
    latitude: Optional[Decimal] = Column(DECIMAL(10, 8), nullable=True)
    longitude: Optional[Decimal] = Column(DECIMAL(11, 8), nullable=True)
    
    # Status
    status: VisitStatus = Column(Enum(VisitStatus), nullable=False, default=VisitStatus.SCHEDULED, index=True)
    
    # Timestamps
    created_at: datetime = Column(DateTime, default=func.now(), nullable=False)
    updated_at: datetime = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships - Lazy loading similar to JPA
    customer = relationship("Customer", back_populates="visits", lazy="select")
    salesperson = relationship("Salesperson", back_populates="visits", lazy="select")
    files: List['VisitFile'] = relationship("VisitFile", back_populates="visit", 
                                          cascade="all, delete-orphan", lazy="select")

    def __init__(self, customer_id: int = None, salesperson_id: int = None, 
                 visit_date: date = None, visit_time: time = None,
                 contacted_persons: str = None, clinical_findings: str = None,
                 additional_notes: str = None, address: str = None,
                 latitude: Decimal = None, longitude: Decimal = None,
                 status: VisitStatus = VisitStatus.SCHEDULED):
        """Constructor similar a Java"""
        self.customer_id = customer_id
        self.salesperson_id = salesperson_id
        self.visit_date = visit_date
        self.visit_time = visit_time
        self.contacted_persons = contacted_persons
        self.clinical_findings = clinical_findings
        self.additional_notes = additional_notes
        self.address = address
        self.latitude = latitude
        self.longitude = longitude
        self.status = status

    def __repr__(self):
        return f"<Visit(id={self.id}, customer_id={self.customer_id}, visit_date={self.visit_date}, status={self.status})>"

    # Getters and Setters (Java style)
    def get_id(self) -> Optional[int]:
        return self.id
    
    def set_id(self, id: int):
        self.id = id
    
    def get_customer_id(self) -> int:
        return self.customer_id
    
    def set_customer_id(self, customer_id: int):
        self.customer_id = customer_id
    
    def get_salesperson_id(self) -> int:
        return self.salesperson_id
    
    def set_salesperson_id(self, salesperson_id: int):
        self.salesperson_id = salesperson_id
    
    def get_visit_date(self) -> date:
        return self.visit_date
    
    def set_visit_date(self, visit_date: date):
        self.visit_date = visit_date
    
    def get_visit_time(self) -> time:
        return self.visit_time
    
    def set_visit_time(self, visit_time: time):
        self.visit_time = visit_time
    
    def get_contacted_persons(self) -> Optional[str]:
        return self.contacted_persons
    
    def set_contacted_persons(self, contacted_persons: str):
        self.contacted_persons = contacted_persons
    
    def get_clinical_findings(self) -> Optional[str]:
        return self.clinical_findings
    
    def set_clinical_findings(self, clinical_findings: str):
        self.clinical_findings = clinical_findings
    
    def get_additional_notes(self) -> Optional[str]:
        return self.additional_notes
    
    def set_additional_notes(self, additional_notes: str):
        self.additional_notes = additional_notes
    
    def get_address(self) -> Optional[str]:
        return self.address
    
    def set_address(self, address: str):
        self.address = address
    
    def get_latitude(self) -> Optional[Decimal]:
        return self.latitude
    
    def set_latitude(self, latitude: Decimal):
        self.latitude = latitude
    
    def get_longitude(self) -> Optional[Decimal]:
        return self.longitude
    
    def set_longitude(self, longitude: Decimal):
        self.longitude = longitude
    
    def get_status(self) -> VisitStatus:
        return self.status
    
    def set_status(self, status: VisitStatus):
        self.status = status
    
    def get_customer(self):
        return self.customer
    
    def set_customer(self, customer):
        self.customer = customer
        if customer:
            self.customer_id = customer.id
    
    def get_salesperson(self):
        return self.salesperson
    
    def set_salesperson(self, salesperson):
        self.salesperson = salesperson
        if salesperson:
            self.salesperson_id = salesperson.id
    
    def get_files(self) -> List['VisitFile']:
        return list(self.files)
    
    def get_created_at(self) -> datetime:
        return self.created_at
    
    def get_updated_at(self) -> datetime:
        return self.updated_at

    # Business Methods
    def is_scheduled(self) -> bool:
        """Verifica si la visita está programada"""
        return self.status == VisitStatus.SCHEDULED
    
    def is_completed(self) -> bool:
        """Verifica si la visita está completada"""
        return self.status == VisitStatus.COMPLETED
    
    def is_cancelled(self) -> bool:
        """Verifica si la visita está cancelada"""
        return self.status == VisitStatus.CANCELLED
    
    def complete_visit(self):
        """Marca la visita como completada"""
        self.status = VisitStatus.COMPLETED
    
    def cancel_visit(self):
        """Marca la visita como cancelada"""
        self.status = VisitStatus.CANCELLED
    
    def get_files_count(self) -> int:
        """Retorna el número de archivos adjuntos"""
        return len(self.files)

    def to_dict(self, include_files: bool = False, include_customer: bool = False, 
                include_salesperson: bool = False) -> dict:
        """Convierte la entidad a diccionario para serialización JSON"""
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
                'full_name': self.salesperson.get_full_name(),
                'territory': self.salesperson.territory
            }
            
        return result