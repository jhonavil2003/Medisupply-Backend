from src.session import db
from datetime import datetime
from typing import Optional
from enum import Enum
try:
    from src.services.integration_service import IntegrationService
except Exception:
    IntegrationService = None

class GoalType(str, Enum):
    """Tipo de objetivo de venta"""
    UNIDADES = 'unidades'
    MONETARIO = 'monetario'

class Region(str, Enum):
    """Regiones geográficas"""
    NORTE = 'Norte'
    SUR = 'Sur'
    OESTE = 'Oeste'
    ESTE = 'Este'

class Quarter(str, Enum):
    """Trimestres del año"""
    Q1 = 'Q1'
    Q2 = 'Q2'
    Q3 = 'Q3'
    Q4 = 'Q4'

class SalespersonGoal(db.Model):
    """Entidad SalespersonGoal - Representa objetivos de venta para vendedores"""
    
    __tablename__ = 'salesperson_goals'

    # Primary Key
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign Keys
    id_vendedor = db.Column(db.String(50), db.ForeignKey('salespersons.employee_id'), nullable=False, index=True)
    id_producto = db.Column(db.String(100), nullable=False, index=True)  # SKU del producto del catalog-service
    
    # Goal Information
    region = db.Column(db.String(20), nullable=False)  # Norte/Sur/Oeste/Este
    trimestre = db.Column(db.String(10), nullable=False)  # Q1/Q2/Q3/Q4
    valor_objetivo = db.Column(db.Numeric(15, 2), nullable=False)  # Valor del objetivo
    tipo = db.Column(db.String(20), nullable=False)  # unidades/monetario
    
    # Timestamps
    fecha_creacion = db.Column(db.DateTime, default=db.func.current_timestamp(), nullable=False)
    fecha_actualizacion = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp(), nullable=False)

    # Relationships
    salesperson = db.relationship("Salesperson", foreign_keys=[id_vendedor], backref="goals", lazy="joined")

    # Composite index for uniqueness
    __table_args__ = (
        db.Index('idx_goal_unique', 'id_vendedor', 'id_producto', 'region', 'trimestre', unique=True),
    )

    def __init__(self, id_vendedor: str = None, id_producto: str = None, region: str = None,
                 trimestre: str = None, valor_objetivo: float = None, tipo: str = None):
        """Constructor similar a Java"""
        self.id_vendedor = id_vendedor
        self.id_producto = id_producto
        self.region = region
        self.trimestre = trimestre
        self.valor_objetivo = valor_objetivo
        self.tipo = tipo

    def __repr__(self):
        return f"<SalespersonGoal(id={self.id}, vendedor='{self.id_vendedor}', producto='{self.id_producto}', trimestre='{self.trimestre}')>"

    # Getters and Setters (Java style)
    def get_id(self) -> Optional[int]:
        return self.id
    
    def set_id(self, id: int):
        self.id = id
    
    def get_id_vendedor(self) -> str:
        return self.id_vendedor
    
    def set_id_vendedor(self, id_vendedor: str):
        self.id_vendedor = id_vendedor
    
    def get_id_producto(self) -> str:
        return self.id_producto
    
    def set_id_producto(self, id_producto: str):
        self.id_producto = id_producto
    
    def get_region(self) -> str:
        return self.region
    
    def set_region(self, region: str):
        self.region = region
    
    def get_trimestre(self) -> str:
        return self.trimestre
    
    def set_trimestre(self, trimestre: str):
        self.trimestre = trimestre
    
    def get_valor_objetivo(self) -> float:
        return float(self.valor_objetivo) if self.valor_objetivo else 0.0
    
    def set_valor_objetivo(self, valor_objetivo: float):
        self.valor_objetivo = valor_objetivo
    
    def get_tipo(self) -> str:
        return self.tipo
    
    def set_tipo(self, tipo: str):
        self.tipo = tipo
    
    def get_fecha_creacion(self) -> datetime:
        return self.fecha_creacion
    
    def get_fecha_actualizacion(self) -> datetime:
        return self.fecha_actualizacion

    # Business Methods
    def is_monetary_goal(self) -> bool:
        """Verifica si el objetivo es monetario"""
        return self.tipo == GoalType.MONETARIO.value

    def is_units_goal(self) -> bool:
        """Verifica si el objetivo es por unidades"""
        return self.tipo == GoalType.UNIDADES.value

    def get_goal_description(self) -> str:
        """Retorna una descripción legible del objetivo"""
        tipo_str = "monetario" if self.is_monetary_goal() else "unidades"
        return f"Objetivo {tipo_str} de {self.valor_objetivo} para {self.trimestre} en región {self.region}"

    def to_dict(self, include_salesperson: bool = False, include_producto: bool = False) -> dict:
        """Convierte la entidad a diccionario para serialización JSON"""
        result = {
            'id': self.id,
            'id_vendedor': self.id_vendedor,
            'id_producto': self.id_producto,
            'region': self.region,
            'trimestre': self.trimestre,
            'valor_objetivo': float(self.valor_objetivo) if self.valor_objetivo else 0.0,
            'tipo': self.tipo,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'fecha_actualizacion': self.fecha_actualizacion.isoformat() if self.fecha_actualizacion else None
        }
        
        if include_salesperson and self.salesperson:
            result['vendedor'] = {
                'employee_id': self.salesperson.employee_id,
                'nombre_completo': self.salesperson.get_full_name(),
                'email': self.salesperson.email
            }
        
        if include_producto and self.id_producto:
            # Obtener información del producto desde catalog-service
            try:
                # Preferir la clase importada a nivel de módulo (facilita mocking en tests)
                if IntegrationService is not None:
                    integration_service = IntegrationService()
                else:
                    from src.services.integration_service import IntegrationService as _IntegrationService
                    integration_service = _IntegrationService()

                producto = integration_service.get_product_by_sku(self.id_producto)
                result['producto'] = {
                    'sku': producto.get('sku'),
                    'name': producto.get('name'),
                    'description': producto.get('description'),
                    'unit_price': producto.get('unit_price'),
                    'is_active': producto.get('is_active')
                }
            except Exception:
                # Si falla la llamada al servicio externo, solo incluimos el SKU
                result['producto'] = {
                    'sku': self.id_producto,
                    'name': None,
                    'description': None,
                    'unit_price': None,
                    'is_active': None
                }
            
        return result

    @staticmethod
    def validate_region(region: str) -> bool:
        """Valida que la región sea válida"""
        return region in [r.value for r in Region]

    @staticmethod
    def validate_quarter(trimestre: str) -> bool:
        """Valida que el trimestre sea válido"""
        return trimestre in [q.value for q in Quarter]

    @staticmethod
    def validate_goal_type(tipo: str) -> bool:
        """Valida que el tipo de objetivo sea válido"""
        return tipo in [t.value for t in GoalType]
