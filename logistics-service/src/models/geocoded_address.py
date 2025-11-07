from src.session import db
from datetime import datetime


class GeocodedAddress(db.Model):
    """
    Modelo para cachear direcciones geocodificadas y evitar llamadas repetidas a Google Maps API.
    Almacena la conversión de direcciones a coordenadas geográficas.
    """
    __tablename__ = 'geocoded_addresses'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Dirección original
    original_address = db.Column(db.String(500), nullable=False, index=True)
    city = db.Column(db.String(100), index=True)
    department = db.Column(db.String(100))
    country = db.Column(db.String(100), default='Colombia')
    
    # Hash de la dirección completa para búsquedas rápidas
    address_hash = db.Column(db.String(64), unique=True, nullable=False, index=True)
    
    # Coordenadas geocodificadas
    latitude = db.Column(db.Numeric(10, 7), nullable=False)
    longitude = db.Column(db.Numeric(10, 7), nullable=False)
    
    # Dirección formateada por Google Maps
    formatted_address = db.Column(db.String(500))
    
    # Información de calidad del geocoding
    confidence_level = db.Column(db.String(20))  # high, medium, low
    location_type = db.Column(db.String(50))  # ROOFTOP, RANGE_INTERPOLATED, GEOMETRIC_CENTER, APPROXIMATE
    
    # Componentes adicionales de la dirección
    street_number = db.Column(db.String(20))
    route = db.Column(db.String(200))
    neighborhood = db.Column(db.String(100))
    postal_code = db.Column(db.String(20))
    
    # Información del proveedor
    provider = db.Column(db.String(50), default='google_maps')  # google_maps, manual, etc.
    place_id = db.Column(db.String(200))  # Google Maps Place ID
    
    # Metadata
    geocoded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    times_used = db.Column(db.Integer, default=0)  # Contador de uso del caché
    last_used_at = db.Column(db.DateTime)
    
    # Validación y calidad
    is_valid = db.Column(db.Boolean, default=True)
    needs_review = db.Column(db.Boolean, default=False)
    
    # Auditoría
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Índices compuestos
    __table_args__ = (
        db.Index('idx_geocoded_city', 'city', 'is_valid'),
        db.Index('idx_geocoded_coordinates', 'latitude', 'longitude'),
    )
    
    @staticmethod
    def generate_address_hash(address: str, city: str, department: str = None):
        """Genera un hash único para la dirección"""
        import hashlib
        
        # Normalizar la dirección
        address_normalized = f"{address.lower().strip()}|{city.lower().strip()}"
        if department:
            address_normalized += f"|{department.lower().strip()}"
        
        # Generar hash SHA-256
        return hashlib.sha256(address_normalized.encode()).hexdigest()
    
    @property
    def coordinates(self):
        """Retorna las coordenadas como tupla"""
        return (float(self.latitude), float(self.longitude))
    
    @property
    def is_high_confidence(self):
        """Indica si el geocoding tiene alta confianza"""
        return self.confidence_level == 'high' and self.location_type == 'ROOFTOP'
    
    def increment_usage(self):
        """Incrementa el contador de uso del caché"""
        self.times_used += 1
        self.last_used_at = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self):
        """Convierte la dirección geocodificada a diccionario"""
        return {
            'id': self.id,
            'original_address': self.original_address,
            'city': self.city,
            'department': self.department,
            'country': self.country,
            'coordinates': {
                'latitude': float(self.latitude),
                'longitude': float(self.longitude),
            },
            'formatted_address': self.formatted_address,
            'quality': {
                'confidence_level': self.confidence_level,
                'location_type': self.location_type,
                'is_high_confidence': self.is_high_confidence,
            },
            'components': {
                'street_number': self.street_number,
                'route': self.route,
                'neighborhood': self.neighborhood,
                'postal_code': self.postal_code,
            },
            'metadata': {
                'provider': self.provider,
                'place_id': self.place_id,
                'geocoded_at': self.geocoded_at.isoformat() if self.geocoded_at else None,
                'times_used': self.times_used,
                'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None,
            },
            'validation': {
                'is_valid': self.is_valid,
                'needs_review': self.needs_review,
            },
            'notes': self.notes,
        }
    
    def __repr__(self):
        return f'<GeocodedAddress {self.city}: {self.original_address[:50]}>'
