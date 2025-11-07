from src.session import db
from datetime import datetime


class Vehicle(db.Model):
    """
    Modelo para representar vehículos de la flota de distribución.
    Incluye información de capacidad, tipo y disponibilidad.
    """
    __tablename__ = 'vehicles'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Información básica del vehículo
    plate = db.Column(db.String(20), unique=True, nullable=False, index=True)
    vehicle_type = db.Column(db.String(50), nullable=False)  # van, truck, refrigerated_truck
    brand = db.Column(db.String(50))
    model = db.Column(db.String(50))
    year = db.Column(db.Integer)
    
    # Capacidades
    capacity_kg = db.Column(db.Numeric(10, 2), nullable=False)  # Capacidad en kg
    capacity_m3 = db.Column(db.Numeric(10, 3), nullable=False)  # Capacidad en m³
    
    # Características especiales
    has_refrigeration = db.Column(db.Boolean, default=False, nullable=False)  # ¿Soporta cadena de frío?
    temperature_min = db.Column(db.Numeric(5, 2))  # Temperatura mínima que soporta
    temperature_max = db.Column(db.Numeric(5, 2))  # Temperatura máxima que soporta
    
    # Restricciones operativas
    max_stops_per_route = db.Column(db.Integer, default=15)  # Máximo de paradas por ruta
    avg_speed_kmh = db.Column(db.Numeric(5, 2), default=40.0)  # Velocidad promedio en km/h
    cost_per_km = db.Column(db.Numeric(8, 2), nullable=False)  # Costo operativo por km
    
    # Asignación a centro de distribución
    home_distribution_center_id = db.Column(
        db.Integer, 
        db.ForeignKey('distribution_centers.id'), 
        nullable=False
    )
    
    # Conductor
    driver_name = db.Column(db.String(100))
    driver_phone = db.Column(db.String(20))
    driver_license = db.Column(db.String(50))
    
    # Estado y disponibilidad
    is_available = db.Column(db.Boolean, default=True, nullable=False, index=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Ubicación actual (opcional, para tracking en tiempo real)
    current_location_lat = db.Column(db.Numeric(10, 7))
    current_location_lng = db.Column(db.Numeric(10, 7))
    last_location_update = db.Column(db.DateTime)
    
    # Mantenimiento
    last_maintenance_date = db.Column(db.Date)
    next_maintenance_date = db.Column(db.Date)
    
    # Auditoría
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = db.Column(db.String(100))
    
    # Relaciones
    distribution_center = db.relationship('DistributionCenter', backref='vehicles')
    delivery_routes = db.relationship('DeliveryRoute', back_populates='vehicle', lazy='dynamic')
    
    # Índices compuestos
    __table_args__ = (
        db.Index('idx_vehicle_availability', 'home_distribution_center_id', 'is_available', 'is_active'),
        db.Index('idx_vehicle_type', 'vehicle_type', 'has_refrigeration'),
    )
    
    @property
    def full_description(self):
        """Descripción completa del vehículo"""
        return f"{self.brand} {self.model} ({self.year}) - {self.plate}"
    
    @property
    def can_handle_cold_chain(self):
        """Indica si puede manejar productos de cadena de frío"""
        return self.has_refrigeration
    
    @property
    def is_ready_for_route(self):
        """Verifica si el vehículo está listo para asignar a una ruta"""
        return self.is_available and self.is_active
    
    def to_dict(self, include_distribution_center=False):
        """Convierte el vehículo a diccionario"""
        data = {
            'id': self.id,
            'plate': self.plate,
            'vehicle_type': self.vehicle_type,
            'brand': self.brand,
            'model': self.model,
            'year': self.year,
            'full_description': self.full_description,
            'capacity': {
                'kg': float(self.capacity_kg) if self.capacity_kg else None,
                'm3': float(self.capacity_m3) if self.capacity_m3 else None,
            },
            'features': {
                'has_refrigeration': self.has_refrigeration,
                'temperature_min': float(self.temperature_min) if self.temperature_min else None,
                'temperature_max': float(self.temperature_max) if self.temperature_max else None,
                'can_handle_cold_chain': self.can_handle_cold_chain,
            },
            'operations': {
                'max_stops_per_route': self.max_stops_per_route,
                'avg_speed_kmh': float(self.avg_speed_kmh) if self.avg_speed_kmh else None,
                'cost_per_km': float(self.cost_per_km) if self.cost_per_km else None,
            },
            'driver': {
                'name': self.driver_name,
                'phone': self.driver_phone,
                'license': self.driver_license,
            },
            'status': {
                'is_available': self.is_available,
                'is_active': self.is_active,
                'is_ready_for_route': self.is_ready_for_route,
            },
            'location': {
                'lat': float(self.current_location_lat) if self.current_location_lat else None,
                'lng': float(self.current_location_lng) if self.current_location_lng else None,
                'last_update': self.last_location_update.isoformat() if self.last_location_update else None,
            },
            'maintenance': {
                'last_date': self.last_maintenance_date.isoformat() if self.last_maintenance_date else None,
                'next_date': self.next_maintenance_date.isoformat() if self.next_maintenance_date else None,
            },
            'home_distribution_center_id': self.home_distribution_center_id,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if include_distribution_center and self.distribution_center:
            data['distribution_center'] = self.distribution_center.to_dict()
        
        return data
    
    def __repr__(self):
        return f'<Vehicle {self.plate} ({self.vehicle_type})>'
