"""
Modelo para rutas de visitas comerciales.

Representa una ruta optimizada para que un vendedor visite múltiples clientes.
Similar a DeliveryRoute pero enfocado en visitas comerciales en lugar de entregas.
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Dict
from sqlalchemy import Enum as SQLEnum
import enum

from src.session import db


class VisitRouteStatus(enum.Enum):
    """Estados de una ruta de visitas"""
    DRAFT = "draft"                    # Ruta generada pero no confirmada
    CONFIRMED = "confirmed"            # Confirmada por el vendedor
    IN_PROGRESS = "in_progress"        # Vendedor en ruta
    COMPLETED = "completed"            # Ruta completada
    CANCELLED = "cancelled"            # Ruta cancelada


class VisitRoute(db.Model):
    """
    Ruta optimizada para visitas comerciales.
    
    Generada por el algoritmo VRP para optimizar el recorrido del vendedor
    visitando múltiples clientes en una jornada.
    """
    __tablename__ = 'visit_routes'

    # Identificación
    id = db.Column(db.Integer, primary_key=True)
    route_code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    
    # Vendedor asignado
    salesperson_id = db.Column(db.Integer, nullable=False, index=True)
    salesperson_name = db.Column(db.String(200))  # Snapshot del nombre
    salesperson_employee_id = db.Column(db.String(50))  # Snapshot del código
    
    # Fecha planeada
    planned_date = db.Column(db.Date, nullable=False, index=True)
    
    # Estado
    status = db.Column(
        SQLEnum(VisitRouteStatus, name='visit_route_status'),
        nullable=False,
        default=VisitRouteStatus.DRAFT,
        index=True
    )
    
    # Métricas de la ruta
    total_stops = db.Column(db.Integer, default=0)
    total_distance_km = db.Column(db.Numeric(10, 2), default=0)
    estimated_duration_minutes = db.Column(db.Integer, default=0)
    
    # Punto de inicio (opcional - normalmente oficina del vendedor)
    start_location_name = db.Column(db.String(200))
    start_latitude = db.Column(db.Numeric(10, 8))
    start_longitude = db.Column(db.Numeric(11, 8))
    
    # Punto de fin (puede ser igual al inicio o diferente)
    end_location_name = db.Column(db.String(200))
    end_latitude = db.Column(db.Numeric(10, 8))
    end_longitude = db.Column(db.Numeric(11, 8))
    
    # Horario de trabajo
    work_start_time = db.Column(db.Time)  # Ej: 08:00
    work_end_time = db.Column(db.Time)    # Ej: 18:00
    
    # Optimización
    optimization_strategy = db.Column(db.String(50), default='minimize_distance')
    optimization_score = db.Column(db.Numeric(5, 2))  # Score de 0-100
    
    # Metadatos de ejecución
    computation_time_seconds = db.Column(db.Numeric(10, 2))
    
    # URL del mapa (Google Maps)
    map_url = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    confirmed_at = db.Column(db.DateTime)  # Cuando se confirma
    started_at = db.Column(db.DateTime)    # Cuando inicia
    completed_at = db.Column(db.DateTime)  # Cuando termina
    
    # Relaciones
    stops = db.relationship(
        'VisitRouteStop',
        back_populates='route',
        cascade='all, delete-orphan',
        order_by='VisitRouteStop.sequence_order',
        lazy='joined'
    )

    def __repr__(self):
        return f"<VisitRoute {self.route_code} - {self.status.value}>"

    def to_dict(self, include_stops: bool = True) -> Dict:
        """
        Convierte el objeto a diccionario.
        
        Args:
            include_stops: Si incluir las paradas en el resultado
        
        Returns:
            Dict con toda la información de la ruta
        """
        result = {
            'id': self.id,
            'route_code': self.route_code,
            'salesperson': {
                'id': self.salesperson_id,
                'name': self.salesperson_name,
                'employee_id': self.salesperson_employee_id
            },
            'planned_date': self.planned_date.isoformat() if self.planned_date else None,
            'status': self.status.value if self.status else None,
            'metrics': {
                'total_stops': self.total_stops,
                'total_distance_km': float(self.total_distance_km) if self.total_distance_km else 0,
                'estimated_duration_minutes': self.estimated_duration_minutes,
                'optimization_score': float(self.optimization_score) if self.optimization_score else None
            },
            'start_location': {
                'name': self.start_location_name,
                'latitude': float(self.start_latitude) if self.start_latitude else None,
                'longitude': float(self.start_longitude) if self.start_longitude else None
            } if self.start_latitude and self.start_longitude else None,
            'end_location': {
                'name': self.end_location_name,
                'latitude': float(self.end_latitude) if self.end_latitude else None,
                'longitude': float(self.end_longitude) if self.end_longitude else None
            } if self.end_latitude and self.end_longitude else None,
            'work_hours': {
                'start': self.work_start_time.strftime('%H:%M') if self.work_start_time else None,
                'end': self.work_end_time.strftime('%H:%M') if self.work_end_time else None
            },
            'optimization_strategy': self.optimization_strategy,
            'computation_time_seconds': float(self.computation_time_seconds) if self.computation_time_seconds else None,
            'map_url': self.map_url,
            'timestamps': {
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'updated_at': self.updated_at.isoformat() if self.updated_at else None,
                'confirmed_at': self.confirmed_at.isoformat() if self.confirmed_at else None,
                'started_at': self.started_at.isoformat() if self.started_at else None,
                'completed_at': self.completed_at.isoformat() if self.completed_at else None
            }
        }
        
        if include_stops:
            result['stops'] = [stop.to_dict() for stop in self.stops]
        
        return result

    def update_metrics(self):
        """Actualiza las métricas calculadas de la ruta"""
        if self.stops:
            self.total_stops = len(self.stops)
            self.total_distance_km = float(sum(
                float(stop.distance_from_previous_km or 0.0)
                for stop in self.stops
            ))
            self.estimated_duration_minutes = int(sum(
                int(stop.estimated_service_time_minutes or 0)
                for stop in self.stops
            ))
            # Agregar tiempo de viaje entre paradas
            # (esto se calcula en el comando de generación)

    def confirm(self):
        """Confirma la ruta"""
        self.status = VisitRouteStatus.CONFIRMED
        self.confirmed_at = datetime.utcnow()

    def start(self):
        """Inicia la ruta"""
        if self.status != VisitRouteStatus.CONFIRMED:
            raise ValueError("Solo se pueden iniciar rutas confirmadas")
        self.status = VisitRouteStatus.IN_PROGRESS
        self.started_at = datetime.utcnow()

    def complete(self):
        """Completa la ruta"""
        if self.status != VisitRouteStatus.IN_PROGRESS:
            raise ValueError("Solo se pueden completar rutas en progreso")
        self.status = VisitRouteStatus.COMPLETED
        self.completed_at = datetime.utcnow()

    def cancel(self):
        """Cancela la ruta"""
        if self.status in [VisitRouteStatus.COMPLETED, VisitRouteStatus.CANCELLED]:
            raise ValueError(f"No se puede cancelar una ruta {self.status.value}")
        self.status = VisitRouteStatus.CANCELLED

    def generate_google_maps_url(self) -> str:
        """
        Genera URL de Google Maps con todas las paradas.
        
        Formato: https://maps.google.com/maps/dir/?api=1&origin=LAT,LNG&waypoints=LAT,LNG|LAT,LNG&destination=LAT,LNG
        
        Returns:
            URL de Google Maps con la ruta completa
        """
        if not self.stops:
            return None
        
        # Punto de inicio
        if self.start_latitude and self.start_longitude:
            origin = f"{self.start_latitude},{self.start_longitude}"
        else:
            # Usar primera parada como origen
            first_stop = self.stops[0]
            origin = f"{first_stop.latitude},{first_stop.longitude}"
        
        # Paradas intermedias
        waypoints = []
        for stop in self.stops:
            if stop.latitude and stop.longitude:
                waypoints.append(f"{stop.latitude},{stop.longitude}")
        
        # Punto de fin
        if self.end_latitude and self.end_longitude:
            destination = f"{self.end_latitude},{self.end_longitude}"
        else:
            # Usar última parada como destino
            destination = waypoints[-1] if waypoints else origin
            waypoints = waypoints[:-1] if len(waypoints) > 1 else []
        
        # Construir URL
        waypoints_str = "|".join(waypoints) if waypoints else ""
        
        if waypoints_str:
            url = f"https://maps.google.com/maps/dir/?api=1&origin={origin}&waypoints={waypoints_str}&destination={destination}"
        else:
            url = f"https://maps.google.com/maps/dir/?api=1&origin={origin}&destination={destination}"
        
        return url

    @staticmethod
    def generate_route_code(salesperson_id: int, planned_date) -> str:
        """
        Genera código único para la ruta.
        
        Formato: VISIT-YYYYMMDD-S{salesperson_id}-{sequence}
        Ejemplo: VISIT-20251120-S002-001
        
        Args:
            salesperson_id: ID del vendedor
            planned_date: Fecha planeada
        
        Returns:
            Código único de ruta
        """
        from datetime import datetime
        
        if isinstance(planned_date, str):
            planned_date = datetime.strptime(planned_date, '%Y-%m-%d').date()
        
        date_str = planned_date.strftime('%Y%m%d')
        
        # Contar rutas existentes para ese vendedor en esa fecha
        existing_count = VisitRoute.query.filter(
            VisitRoute.salesperson_id == salesperson_id,
            VisitRoute.planned_date == planned_date
        ).count()
        
        sequence = existing_count + 1
        
        return f"VISIT-{date_str}-S{salesperson_id:03d}-{sequence:03d}"
