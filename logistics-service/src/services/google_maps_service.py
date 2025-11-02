"""
Google Maps Service para integración con Geocoding API y Distance Matrix API.
Implementa caché de direcciones para reducir llamadas a la API.
"""

import os
import googlemaps
import logging
from typing import List, Dict, Tuple, Optional
from datetime import datetime
from src.models.geocoded_address import GeocodedAddress
from src.session import db

logger = logging.getLogger(__name__)


class GoogleMapsService:
    """
    Servicio para integración con Google Maps API.
    Proporciona funciones de geocodificación y cálculo de distancias.
    """
    
    def __init__(self):
        """Inicializa el cliente de Google Maps"""
        self.api_key = os.getenv('GOOGLE_MAPS_API_KEY')
        if not self.api_key:
            raise ValueError("GOOGLE_MAPS_API_KEY no está configurado en las variables de entorno")
        
        self.client = googlemaps.Client(key=self.api_key)
        self.geocoding_enabled = os.getenv('GOOGLE_MAPS_GEOCODING_ENABLED', 'true').lower() == 'true'
        self.distance_matrix_enabled = os.getenv('GOOGLE_MAPS_DISTANCE_MATRIX_ENABLED', 'true').lower() == 'true'
        
        logger.info(f"✅ Google Maps Service inicializado (Geocoding: {self.geocoding_enabled}, Distance Matrix: {self.distance_matrix_enabled})")
    
    def geocode_address(
        self, 
        address: str, 
        city: str, 
        department: str = None, 
        country: str = 'Colombia',
        use_cache: bool = True
    ) -> Dict:
        """
        Convierte una dirección en coordenadas geográficas.
        
        Args:
            address: Dirección a geocodificar (ej: "Calle 100 # 15-20")
            city: Ciudad (ej: "Bogotá")
            department: Departamento/Estado (ej: "Cundinamarca")
            country: País (default: "Colombia")
            use_cache: Si True, busca primero en caché
        
        Returns:
            Dict con:
            - lat: Latitud
            - lng: Longitud
            - formatted_address: Dirección formateada
            - confidence: Nivel de confianza ('high', 'medium', 'low')
            - from_cache: Si se obtuvo del caché
        
        Raises:
            ValueError: Si no se puede geocodificar la dirección
        """
        
        if not self.geocoding_enabled:
            raise ValueError("Geocoding API está deshabilitado")
        
        # Generar hash de la dirección para búsqueda en caché
        address_hash = GeocodedAddress.generate_address_hash(address, city, department)
        
        # Buscar en caché si está habilitado
        if use_cache:
            cached = GeocodedAddress.query.filter_by(
                address_hash=address_hash,
                is_valid=True
            ).first()
            
            if cached:
                logger.info(f"📍 Geocoding desde caché: {address}, {city}")
                cached.increment_usage()
                
                return {
                    'lat': float(cached.latitude),
                    'lng': float(cached.longitude),
                    'formatted_address': cached.formatted_address,
                    'confidence': cached.confidence_level,
                    'location_type': cached.location_type,
                    'from_cache': True,
                    'place_id': cached.place_id,
                }
        
        # Construir dirección completa
        full_address = f"{address}, {city}"
        if department:
            full_address += f", {department}"
        full_address += f", {country}"
        
        logger.info(f"🌍 Geocoding desde Google Maps API: {full_address}")
        
        try:
            # Llamar a Google Maps Geocoding API
            geocode_result = self.client.geocode(full_address)
            
            if not geocode_result:
                raise ValueError(f"No se pudo geocodificar la dirección: {full_address}")
            
            # Tomar el primer resultado
            result = geocode_result[0]
            
            # Extraer coordenadas
            location = result['geometry']['location']
            lat = location['lat']
            lng = location['lng']
            
            # Extraer información de calidad
            location_type = result['geometry']['location_type']
            formatted_address = result['formatted_address']
            place_id = result.get('place_id')
            
            # Determinar nivel de confianza
            confidence = self._determine_confidence(location_type, result)
            
            # Extraer componentes de la dirección
            components = self._extract_address_components(result['address_components'])
            
            # Guardar en caché
            if use_cache:
                geocoded = GeocodedAddress(
                    original_address=address,
                    city=city,
                    department=department or components.get('administrative_area_level_1'),
                    country=country,
                    address_hash=address_hash,
                    latitude=lat,
                    longitude=lng,
                    formatted_address=formatted_address,
                    confidence_level=confidence,
                    location_type=location_type,
                    street_number=components.get('street_number'),
                    route=components.get('route'),
                    neighborhood=components.get('neighborhood'),
                    postal_code=components.get('postal_code'),
                    provider='google_maps',
                    place_id=place_id,
                    times_used=1,
                    last_used_at=datetime.utcnow(),
                )
                
                db.session.add(geocoded)
                db.session.commit()
                
                logger.info(f"💾 Dirección guardada en caché: {formatted_address}")
            
            return {
                'lat': lat,
                'lng': lng,
                'formatted_address': formatted_address,
                'confidence': confidence,
                'location_type': location_type,
                'from_cache': False,
                'place_id': place_id,
                'components': components,
            }
            
        except Exception as e:
            logger.error(f"❌ Error en geocoding: {str(e)}")
            raise ValueError(f"Error al geocodificar dirección: {str(e)}")
    
    def batch_geocode(self, addresses: List[Dict], use_cache: bool = True) -> List[Dict]:
        """
        Geocodifica múltiples direcciones.
        
        Args:
            addresses: Lista de dicts con keys: 'address', 'city', 'department' (opcional)
            use_cache: Si True, usa caché
        
        Returns:
            Lista de resultados de geocodificación
        """
        
        results = []
        
        for addr_data in addresses:
            try:
                result = self.geocode_address(
                    address=addr_data['address'],
                    city=addr_data['city'],
                    department=addr_data.get('department'),
                    use_cache=use_cache
                )
                
                result['original_data'] = addr_data
                results.append(result)
                
            except Exception as e:
                logger.warning(f"⚠️ No se pudo geocodificar: {addr_data.get('address')} - {str(e)}")
                results.append({
                    'error': str(e),
                    'original_data': addr_data,
                    'lat': None,
                    'lng': None,
                })
        
        logger.info(f"📍 Batch geocoding completado: {len(results)} direcciones procesadas")
        return results
    
    def get_distance_matrix(
        self, 
        origins: List[Tuple[float, float]], 
        destinations: List[Tuple[float, float]],
        mode: str = 'driving',
        departure_time: datetime = None
    ) -> Dict:
        """
        Obtiene matriz de distancias y tiempos entre orígenes y destinos.
        
        Args:
            origins: Lista de tuplas (lat, lng) de orígenes
            destinations: Lista de tuplas (lat, lng) de destinos
            mode: Modo de transporte ('driving', 'walking', 'bicycling', 'transit')
            departure_time: Tiempo de salida (para considerar tráfico)
        
        Returns:
            Dict con:
            - distances_km: Matriz de distancias en kilómetros
            - durations_minutes: Matriz de tiempos en minutos
            - status: Estado de la respuesta
        """
        
        if not self.distance_matrix_enabled:
            raise ValueError("Distance Matrix API está deshabilitado")
        
        logger.info(f"🗺️ Calculando Distance Matrix: {len(origins)} orígenes × {len(destinations)} destinos")
        
        try:
            # Llamar a Google Maps Distance Matrix API
            matrix_result = self.client.distance_matrix(
                origins=origins,
                destinations=destinations,
                mode=mode,
                departure_time=departure_time or 'now',
                language='es',
                units='metric'
            )
            
            if matrix_result['status'] != 'OK':
                raise ValueError(f"Error en Distance Matrix API: {matrix_result['status']}")
            
            # Procesar resultados
            rows = matrix_result['rows']
            
            distances_km = []
            durations_minutes = []
            
            for row in rows:
                distance_row = []
                duration_row = []
                
                for element in row['elements']:
                    if element['status'] == 'OK':
                        # Distancia en km
                        distance_km = element['distance']['value'] / 1000  # meters to km
                        distance_row.append(round(distance_km, 2))
                        
                        # Duración en minutos
                        duration_minutes = element['duration']['value'] / 60  # seconds to minutes
                        duration_row.append(round(duration_minutes))
                    else:
                        # Si no se puede calcular, usar valores muy grandes
                        distance_row.append(9999999)
                        duration_row.append(9999999)
                
                distances_km.append(distance_row)
                durations_minutes.append(duration_row)
            
            logger.info(f"✅ Distance Matrix calculado exitosamente")
            
            return {
                'distances_km': distances_km,
                'durations_minutes': durations_minutes,
                'status': 'OK',
                'origins_count': len(origins),
                'destinations_count': len(destinations),
            }
            
        except Exception as e:
            logger.error(f"❌ Error en Distance Matrix: {str(e)}")
            raise ValueError(f"Error al calcular Distance Matrix: {str(e)}")
    
    def calculate_route_polyline(self, waypoints: List[Tuple[float, float]]) -> str:
        """
        Genera una polyline codificada para visualización en mapa.
        
        Args:
            waypoints: Lista de tuplas (lat, lng) que forman la ruta
        
        Returns:
            String con polyline codificada
        """
        
        if len(waypoints) < 2:
            return ""
        
        try:
            # Usar Directions API para obtener polyline
            origin = waypoints[0]
            destination = waypoints[-1]
            waypoints_middle = waypoints[1:-1] if len(waypoints) > 2 else None
            
            directions_result = self.client.directions(
                origin=origin,
                destination=destination,
                waypoints=waypoints_middle,
                mode='driving',
                language='es'
            )
            
            if directions_result:
                # Extraer polyline del primer resultado
                polyline = directions_result[0]['overview_polyline']['points']
                logger.info(f"🗺️ Polyline generado para {len(waypoints)} waypoints")
                return polyline
            
            return ""
            
        except Exception as e:
            logger.error(f"❌ Error generando polyline: {str(e)}")
            return ""
    
    def _determine_confidence(self, location_type: str, geocode_result: Dict) -> str:
        """
        Determina el nivel de confianza del geocoding.
        
        Args:
            location_type: Tipo de ubicación de Google Maps
            geocode_result: Resultado completo del geocoding
        
        Returns:
            'high', 'medium', o 'low'
        """
        
        # ROOFTOP es el más preciso (coordenadas exactas del edificio)
        if location_type == 'ROOFTOP':
            return 'high'
        
        # RANGE_INTERPOLATED es interpolación entre direcciones conocidas
        elif location_type == 'RANGE_INTERPOLATED':
            return 'medium'
        
        # GEOMETRIC_CENTER es el centro de una región (calle, barrio)
        elif location_type == 'GEOMETRIC_CENTER':
            return 'medium'
        
        # APPROXIMATE es aproximado (ciudad, región)
        else:
            return 'low'
    
    def _extract_address_components(self, components: List[Dict]) -> Dict:
        """
        Extrae componentes específicos de la dirección.
        
        Args:
            components: Lista de componentes de Google Maps
        
        Returns:
            Dict con componentes extraídos
        """
        
        result = {}
        
        type_mapping = {
            'street_number': 'street_number',
            'route': 'route',
            'neighborhood': 'neighborhood',
            'locality': 'city',
            'administrative_area_level_1': 'administrative_area_level_1',
            'postal_code': 'postal_code',
        }
        
        for component in components:
            for comp_type in component['types']:
                if comp_type in type_mapping:
                    key = type_mapping[comp_type]
                    result[key] = component['long_name']
        
        return result


# Instancia global del servicio (singleton)
_google_maps_service = None


def get_google_maps_service() -> GoogleMapsService:
    """
    Obtiene la instancia singleton del servicio de Google Maps.
    """
    global _google_maps_service
    
    if _google_maps_service is None:
        _google_maps_service = GoogleMapsService()
    
    return _google_maps_service
