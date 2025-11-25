# python
from datetime import datetime
from src.session import db


class Salesperson(db.Model):
    """Salesperson model representing a vendedor."""

    __tablename__ = 'salespersons'

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, index=True)
    phone = db.Column(db.String(20))
    territory = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<Salesperson {self.employee_id}: {self.get_full_name()}>'

    def get_full_name(self):
        """Retornar nombre completo usado por Customer.to_dict()."""
        return f'{self.first_name or ""} {self.last_name or ""}'.strip()

    def to_dict(self, include_assigned_customers=False):
        """Convertir salesperson a diccionario. Si include_assigned_customers=True incluye clientes asignados."""
        result = {
            'id': self.id,
            'employee_id': self.employee_id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.get_full_name(),
            'email': self.email,
            'phone': self.phone,
            'territory': self.territory,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

        if include_assigned_customers:
            # `assigned_customers` es creado por el backref en Customer.salesperson
            assigned = getattr(self, 'assigned_customers', None)
            if assigned is not None:
                try:
                    result['assigned_customers'] = [c.to_dict() for c in assigned]
                except TypeError:
                    # si es un query loader (lazy='dynamic') convertir con .all()
                    result['assigned_customers'] = [c.to_dict() for c in assigned.all()]
            else:
                result['assigned_customers'] = []

        return result
