from sqlalchemy import Column, Integer, String, Date, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.session import Base
from datetime import datetime, date
from typing import List, Optional


class Salesperson(Base):
    """Entidad Salesperson - Representa un vendedor en el sistema"""
    
    __tablename__ = 'salespersons'

    # Primary Key
    id: int = Column(Integer, primary_key=True, autoincrement=True)
    
    # Basic Information
    employee_id: str = Column(String(50), unique=True, nullable=False, index=True)
    first_name: str = Column(String(100), nullable=False)
    last_name: str = Column(String(100), nullable=False)
    email: str = Column(String(150), unique=True, nullable=False)
    phone: Optional[str] = Column(String(20), nullable=True)
    territory: Optional[str] = Column(String(100), nullable=True)
    hire_date: Optional[date] = Column(Date, nullable=True)
    is_active: bool = Column(Boolean, nullable=False, default=True, index=True)
    
    # Timestamps
    created_at: datetime = Column(DateTime, default=func.now(), nullable=False)
    updated_at: datetime = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships - Lazy loading similar to JPA
    visits: List['Visit'] = relationship("Visit", back_populates="salesperson", lazy="dynamic")

    def __init__(self, employee_id: str = None, first_name: str = None, last_name: str = None, 
                 email: str = None, phone: str = None, territory: str = None, 
                 hire_date: date = None, is_active: bool = True):
        """Constructor similar a Java"""
        self.employee_id = employee_id
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.phone = phone
        self.territory = territory
        self.hire_date = hire_date
        self.is_active = is_active

    def __repr__(self):
        return f"<Salesperson(id={self.id}, employee_id='{self.employee_id}', name='{self.get_full_name()}')>"

    # Getters and Setters (Java style)
    def get_id(self) -> Optional[int]:
        return self.id
    
    def set_id(self, id: int):
        self.id = id
    
    def get_employee_id(self) -> str:
        return self.employee_id
    
    def set_employee_id(self, employee_id: str):
        self.employee_id = employee_id
    
    def get_first_name(self) -> str:
        return self.first_name
    
    def set_first_name(self, first_name: str):
        self.first_name = first_name
    
    def get_last_name(self) -> str:
        return self.last_name
    
    def set_last_name(self, last_name: str):
        self.last_name = last_name
        
    def get_full_name(self) -> str:
        """Obtiene el nombre completo"""
        return f"{self.first_name} {self.last_name}"
    
    def get_email(self) -> str:
        return self.email
    
    def set_email(self, email: str):
        self.email = email
    
    def get_phone(self) -> Optional[str]:
        return self.phone
    
    def set_phone(self, phone: str):
        self.phone = phone
    
    def get_territory(self) -> Optional[str]:
        return self.territory
    
    def set_territory(self, territory: str):
        self.territory = territory
    
    def get_hire_date(self) -> Optional[date]:
        return self.hire_date
    
    def set_hire_date(self, hire_date: date):
        self.hire_date = hire_date
    
    def is_is_active(self) -> bool:
        return self.is_active
    
    def set_is_active(self, is_active: bool):
        self.is_active = is_active
    
    def get_visits(self) -> List['Visit']:
        return list(self.visits)
    
    def get_created_at(self) -> datetime:
        return self.created_at
    
    def get_updated_at(self) -> datetime:
        return self.updated_at

    # Business Methods
    def get_active_visits_count(self) -> int:
        """Retorna el número de visitas activas (programadas o completadas)"""
        from .visit_status import VisitStatus
        return len([v for v in self.visits if v.status in [VisitStatus.SCHEDULED, VisitStatus.COMPLETED]])

    def get_territory_display(self) -> str:
        """Retorna el territorio en formato legible"""
        return self.territory if self.territory else "Sin territorio asignado"

    def to_dict(self, include_visits: bool = False) -> dict:
        """Convierte la entidad a diccionario para serialización JSON"""
        result = {
            'id': self.id,
            'employee_id': self.employee_id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.get_full_name(),
            'email': self.email,
            'phone': self.phone,
            'territory': self.territory,
            'hire_date': self.hire_date.isoformat() if self.hire_date else None,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_visits:
            result['visits'] = [visit.to_dict() for visit in self.visits]
            
        return result