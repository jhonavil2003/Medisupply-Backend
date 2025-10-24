from src.session import db
from datetime import datetime

class WarehouseLocation(db.Model):
    """
    Modelo para representar ubicaciones físicas dentro de un centro de distribución.
    Cada ubicación corresponde a un espacio específico donde se almacenan productos.
    """
    __tablename__ = 'warehouse_locations'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Relación con el centro de distribución
    distribution_center_id = db.Column(db.Integer, db.ForeignKey('distribution_centers.id'), nullable=False)
    
    # Tipo de zona: 'refrigerated' (refrigerado/cadena de frío) o 'ambient' (ambiente)
    zone_type = db.Column(db.String(20), nullable=False, index=True)
    
    # Ubicación física específica
    aisle = db.Column(db.String(20), nullable=False)  # Pasillo (ej: "A", "B1", "C-02")
    shelf = db.Column(db.String(20), nullable=False)  # Estantería (ej: "E1", "Rack-05")
    level_position = db.Column(db.String(20), nullable=False)  # Nivel/Posición (ej: "N3-P2", "L2")
    
    # Control de temperatura para zonas refrigeradas
    temperature_min = db.Column(db.Numeric(5, 2))  # Temperatura mínima en °C
    temperature_max = db.Column(db.Numeric(5, 2))  # Temperatura máxima en °C
    current_temperature = db.Column(db.Numeric(5, 2))  # Temperatura actual en °C
    
    # Capacidad y estado
    capacity_units = db.Column(db.Integer)  # Capacidad máxima en unidades
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)
    
    # Descripción adicional
    notes = db.Column(db.Text)
    
    # Auditoría
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relaciones
    distribution_center = db.relationship('DistributionCenter', backref='warehouse_locations')
    product_batches = db.relationship('ProductBatch', back_populates='location', lazy='dynamic')
    
    # Índices compuestos para búsquedas rápidas
    __table_args__ = (
        db.UniqueConstraint('distribution_center_id', 'aisle', 'shelf', 'level_position', 
                          name='uix_location_position'),
        db.Index('idx_dc_zone', 'distribution_center_id', 'zone_type'),
        db.Index('idx_location_active', 'distribution_center_id', 'is_active'),
    )
    
    @property
    def location_code(self):
        """Código completo de la ubicación"""
        return f"{self.aisle}-{self.shelf}-{self.level_position}"
    
    @property
    def is_refrigerated(self):
        """Indica si la ubicación es refrigerada"""
        return self.zone_type == 'refrigerated'
    
    @property
    def temperature_in_range(self):
        """Verifica si la temperatura actual está dentro del rango permitido"""
        if not self.is_refrigerated or self.current_temperature is None:
            return True
        
        if self.temperature_min is not None and self.current_temperature < self.temperature_min:
            return False
        
        if self.temperature_max is not None and self.current_temperature > self.temperature_max:
            return False
        
        return True
    
    def to_dict(self, include_temperature=True):
        """Convierte la ubicación a diccionario"""
        data = {
            'id': self.id,
            'distribution_center_id': self.distribution_center_id,
            'zone_type': self.zone_type,
            'is_refrigerated': self.is_refrigerated,
            'location': {
                'aisle': self.aisle,
                'shelf': self.shelf,
                'level_position': self.level_position,
                'code': self.location_code,
            },
            'capacity_units': self.capacity_units,
            'is_active': self.is_active,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if include_temperature and self.is_refrigerated:
            data['temperature'] = {
                'min': float(self.temperature_min) if self.temperature_min else None,
                'max': float(self.temperature_max) if self.temperature_max else None,
                'current': float(self.current_temperature) if self.current_temperature else None,
                'in_range': self.temperature_in_range,
            }
        
        return data
    
    def __repr__(self):
        return f'<WarehouseLocation DC:{self.distribution_center_id} {self.location_code} ({self.zone_type})>'
