from sqlalchemy import Column, Integer, String, Date, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from session import Base


class Salesperson(Base):
    __tablename__ = 'salespersons'

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(String(50), unique=True, nullable=False, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    phone = Column(String(20), nullable=True)
    territory = Column(String(100), nullable=True)
    hire_date = Column(Date, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relaciones
    visits = relationship("Visit", back_populates="salesperson")

    def __repr__(self):
        return f"<Salesperson(id={self.id}, employee_id='{self.employee_id}', name='{self.first_name} {self.last_name}')>"

    def to_dict(self, include_visits=False):
        """Convierte el modelo a diccionario para serialización JSON"""
        result = {
            'id': self.id,
            'employee_id': self.employee_id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': f"{self.first_name} {self.last_name}",
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

    @staticmethod
    def from_dict(data):
        """Crea una instancia de Salesperson desde un diccionario"""
        salesperson = Salesperson()
        salesperson.employee_id = data.get('employee_id')
        salesperson.first_name = data.get('first_name')
        salesperson.last_name = data.get('last_name')
        salesperson.email = data.get('email')
        salesperson.phone = data.get('phone')
        salesperson.territory = data.get('territory')
        salesperson.hire_date = data.get('hire_date')
        
        # Manejo del estado activo
        is_active = data.get('is_active')
        if is_active is not None:
            salesperson.is_active = bool(is_active)
            
        return salesperson

    def get_active_visits_count(self):
        """Retorna el número de visitas activas (programadas o completadas)"""
        from .visit import VisitStatus
        return len([v for v in self.visits if v.status in [VisitStatus.SCHEDULED, VisitStatus.COMPLETED]])

    def get_territory_display(self):
        """Retorna el territorio en formato legible"""
        return self.territory if self.territory else "Sin territorio asignado"