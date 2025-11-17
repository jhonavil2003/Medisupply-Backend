"""
Modelo para paradas en rutas de visitas comerciales.

Representa cada cliente que el vendedor visitará en la ruta optimizada.
"""

from datetime import datetime, time
from decimal import Decimal
from typing import Dict

from src.session import db


class VisitRouteStop(db.Model):
    """
    Parada en una ruta de visitas.
    
    Representa un cliente específico que será visitado en la ruta,
    incluyendo el orden de visita, tiempos estimados y distancias.
    """
    __tablename__ = 'visit_route_stops'

    # Identificación
    id = db.Column(db.Integer, primary_key=True)
    route_id = db.Column(db.Integer, db.ForeignKey('visit_routes.id'), nullable=False, index=True)
    
    # Orden en la ruta
    sequence_order = db.Column(db.Integer, nullable=False)
    
    # Cliente a visitar (ID desde sales-service)
    customer_id = db.Column(db.Integer, nullable=False, index=True)
    customer_name = db.Column(db.String(200), nullable=False)
    customer_document = db.Column(db.String(50))  # Snapshot del documento
    customer_type = db.Column(db.String(50))      # Snapshot del tipo
    
    # Visita relacionada (si ya se creó en sales-service)
    visit_id = db.Column(db.Integer, index=True)  # ID de la visita en sales-service
    
    # Ubicación
    address = db.Column(db.String(500))
    neighborhood = db.Column(db.String(100))
    city = db.Column(db.String(100))
    department = db.Column(db.String(100))
    latitude = db.Column(db.Numeric(10, 8), nullable=False)
    longitude = db.Column(db.Numeric(11, 8), nullable=False)
    
    # Información de contacto (snapshot)
    contact_name = db.Column(db.String(200))
    contact_phone = db.Column(db.String(50))
    contact_email = db.Column(db.String(200))
    
    # Tiempos estimados
    estimated_arrival_time = db.Column(db.DateTime)  # Hora estimada de llegada
    estimated_departure_time = db.Column(db.DateTime)  # Hora estimada de salida
    estimated_service_time_minutes = db.Column(db.Integer, default=30)  # Tiempo de visita
    
    # Tiempos reales (cuando se completa)
    actual_arrival_time = db.Column(db.DateTime)
    actual_departure_time = db.Column(db.DateTime)
    actual_service_time_minutes = db.Column(db.Integer)
    
    # Distancia desde la parada anterior
    distance_from_previous_km = db.Column(db.Numeric(10, 2), default=0)
    travel_time_from_previous_minutes = db.Column(db.Integer, default=0)
    
    # Estado de la visita
    is_completed = db.Column(db.Boolean, default=False)
    is_skipped = db.Column(db.Boolean, default=False)
    skip_reason = db.Column(db.String(500))
    
    # Notas
    notes = db.Column(db.Text)  # Notas pre-visita
    visit_notes = db.Column(db.Text)  # Notas post-visita
    
    # Timestamps
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime)

    # Relación con la ruta
    route = db.relationship('VisitRoute', back_populates='stops')

    def __repr__(self):
        return f"<VisitRouteStop {self.sequence_order}: {self.customer_name}>"

    def to_dict(self, include_route: bool = False) -> Dict:
        """
        Convierte el objeto a diccionario.
        
        Args:
            include_route: Si incluir información de la ruta padre
        
        Returns:
            Dict con toda la información de la parada
        """
        result = {
            'id': self.id,
            'route_id': self.route_id,
            'sequence_order': self.sequence_order,
            'customer': {
                'id': self.customer_id,
                'name': self.customer_name,
                'document': self.customer_document,
                'type': self.customer_type,
                'contact': {
                    'name': self.contact_name,
                    'phone': self.contact_phone,
                    'email': self.contact_email
                } if self.contact_name else None
            },
            'visit_id': self.visit_id,
            'location': {
                'address': self.address,
                'neighborhood': self.neighborhood,
                'city': self.city,
                'department': self.department,
                'latitude': float(self.latitude) if self.latitude else None,
                'longitude': float(self.longitude) if self.longitude else None
            },
            'estimated_times': {
                'arrival': self.estimated_arrival_time.isoformat() if self.estimated_arrival_time else None,
                'departure': self.estimated_departure_time.isoformat() if self.estimated_departure_time else None,
                'service_minutes': self.estimated_service_time_minutes
            },
            'actual_times': {
                'arrival': self.actual_arrival_time.isoformat() if self.actual_arrival_time else None,
                'departure': self.actual_departure_time.isoformat() if self.actual_departure_time else None,
                'service_minutes': self.actual_service_time_minutes
            } if self.actual_arrival_time else None,
            'distance_metrics': {
                'from_previous_km': float(self.distance_from_previous_km) if self.distance_from_previous_km else 0,
                'travel_time_minutes': self.travel_time_from_previous_minutes
            },
            'status': {
                'is_completed': self.is_completed,
                'is_skipped': self.is_skipped,
                'skip_reason': self.skip_reason
            },
            'notes': self.notes,
            'visit_notes': self.visit_notes,
            'timestamps': {
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'updated_at': self.updated_at.isoformat() if self.updated_at else None,
                'completed_at': self.completed_at.isoformat() if self.completed_at else None
            }
        }
        
        if include_route and self.route:
            result['route'] = {
                'id': self.route.id,
                'route_code': self.route.route_code,
                'status': self.route.status.value if self.route.status else None
            }
        
        return result

    def complete(self, actual_arrival: datetime = None, actual_departure: datetime = None, notes: str = None):
        """
        Marca la parada como completada.
        
        Args:
            actual_arrival: Hora real de llegada
            actual_departure: Hora real de salida
            notes: Notas de la visita
        """
        self.is_completed = True
        self.completed_at = datetime.utcnow()
        
        if actual_arrival:
            self.actual_arrival_time = actual_arrival
        
        if actual_departure:
            self.actual_departure_time = actual_departure
            
            # Calcular tiempo real de servicio
            if self.actual_arrival_time:
                delta = actual_departure - self.actual_arrival_time
                self.actual_service_time_minutes = int(delta.total_seconds() / 60)
        
        if notes:
            self.visit_notes = notes

    def skip(self, reason: str):
        """
        Marca la parada como omitida.
        
        Args:
            reason: Razón por la cual se omitió
        """
        self.is_skipped = True
        self.skip_reason = reason
        self.completed_at = datetime.utcnow()

    def get_google_maps_link(self) -> str:
        """
        Genera enlace directo a Google Maps para esta ubicación.
        
        Returns:
            URL de Google Maps
        """
        if self.latitude and self.longitude:
            return f"https://maps.google.com/?q={self.latitude},{self.longitude}"
        return None

    @property
    def estimated_duration_total_minutes(self) -> int:
        """
        Duración total estimada (viaje + servicio).
        
        Returns:
            Minutos totales estimados para esta parada
        """
        return (self.travel_time_from_previous_minutes or 0) + (self.estimated_service_time_minutes or 0)

    @property
    def actual_duration_total_minutes(self) -> int:
        """
        Duración total real (si está completada).
        
        Returns:
            Minutos totales reales, o None si no está completada
        """
        if not self.actual_arrival_time or not self.actual_departure_time:
            return None
        
        delta = self.actual_departure_time - self.actual_arrival_time
        return int(delta.total_seconds() / 60)

    @property
    def is_pending(self) -> bool:
        """Verifica si la parada está pendiente"""
        return not self.is_completed and not self.is_skipped

    @property
    def status_label(self) -> str:
        """Retorna etiqueta de estado en español"""
        if self.is_completed:
            return "Completada"
        elif self.is_skipped:
            return "Omitida"
        else:
            return "Pendiente"
