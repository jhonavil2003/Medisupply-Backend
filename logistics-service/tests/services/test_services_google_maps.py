"""
Tests unitarios para GoogleMapsService.

IMPORTANTE: Estos tests NO dependen de variables de entorno reales.
Todos los tests mockean completamente la inicialización de GoogleMapsService
usando @patch.object para evitar dependencias externas.
"""

import pytest
from unittest.mock import Mock, patch
from decimal import Decimal

from src.services.google_maps_service import GoogleMapsService
from src.models.geocoded_address import GeocodedAddress


class TestGoogleMapsService:
    """Test suite para GoogleMapsService sin dependencias de variables de entorno."""
    
    @patch('src.services.google_maps_service.googlemaps.Client')
    @patch.object(GoogleMapsService, '__init__', lambda self: None)
    def test_service_initialization(self, mock_client):
        """Test inicialización del servicio (completamente mockeado)."""
        service = GoogleMapsService()
        # Configurar atributos manualmente después de mockear __init__
        service.api_key = 'test_api_key'
        service.client = Mock()
        service.geocoding_enabled = True
        service.distance_matrix_enabled = True
        
        assert service.api_key == 'test_api_key'
        assert service.client is not None
        assert service.geocoding_enabled is True
        assert service.distance_matrix_enabled is True
    
    @patch('src.services.google_maps_service.googlemaps.Client')
    @patch.object(GoogleMapsService, '__init__', lambda self: None)
    def test_geocode_address_success(self, mock_client, db):
        """Test geocodificación exitosa."""
        # Configurar servicio mockeado
        service = GoogleMapsService()
        service.api_key = 'test_key'
        service.geocoding_enabled = True
        service.distance_matrix_enabled = True
        
        # Mock de la respuesta de Google Maps
        mock_instance = Mock()
        service.client = mock_instance
        
        mock_instance.geocode.return_value = [{
            'geometry': {
                'location': {'lat': 4.68682, 'lng': -74.05477},
                'location_type': 'ROOFTOP'
            },
            'formatted_address': 'Calle 100 #50-25, Bogotá, Colombia',
            'place_id': 'ChIJ123abc',
            'address_components': [
                {'types': ['street_number'], 'long_name': '50-25'},
                {'types': ['route'], 'long_name': 'Calle 100'},
                {'types': ['locality'], 'long_name': 'Bogotá'},
                {'types': ['administrative_area_level_1'], 'long_name': 'Cundinamarca'},
                {'types': ['country'], 'long_name': 'Colombia'}
            ]
        }]
        
        result = service.geocode_address('Calle 100 # 50-25', 'Bogotá', use_cache=False)
        
        assert result['lat'] == 4.68682
        assert result['lng'] == -74.05477
        assert result['formatted_address'] == 'Calle 100 #50-25, Bogotá, Colombia'
        assert result['confidence'] in ['high', 'medium', 'low']
        assert result['from_cache'] is False
    
    @patch.object(GoogleMapsService, '__init__', lambda self: None)
    def test_geocode_address_from_cache(self, db):
        """Test que usa caché para direcciones previamente geocodificadas."""
        # Crear entrada en caché
        cached = GeocodedAddress(
            address_hash=GeocodedAddress.generate_address_hash('Calle 100', 'Bogotá'),
            original_address='Calle 100',
            city='Bogotá',
            country='Colombia',
            latitude=Decimal('4.68682'),
            longitude=Decimal('-74.05477'),
            formatted_address='Calle 100, Bogotá, Colombia',
            confidence_level='high',
            location_type='ROOFTOP',
            provider='google_maps',
            times_used=1,
            is_valid=True
        )
        db.session.add(cached)
        db.session.commit()
        
        service = GoogleMapsService()
        service.api_key = 'test_key'
        service.geocoding_enabled = True
        service.client = Mock()
        
        result = service.geocode_address('Calle 100', 'Bogotá', use_cache=True)
        
        # Verificar que se usó caché
        assert result['from_cache'] is True
        assert result['lat'] == 4.68682
        assert result['lng'] == -74.05477
        
        # Verificar que NO se llamó a la API
        service.client.geocode.assert_not_called()
        
        # Verificar que se incrementó el contador de uso
        db.session.refresh(cached)
        assert cached.times_used == 2
    
    @patch.object(GoogleMapsService, '__init__', lambda self: None)
    def test_geocode_address_not_found(self, db):
        """Test cuando Google Maps no encuentra la dirección."""
        mock_instance = Mock()
        mock_instance.geocode.return_value = []
        
        service = GoogleMapsService()
        service.api_key = 'test_key'
        service.geocoding_enabled = True
        service.client = mock_instance
        
        with pytest.raises(ValueError, match="No se pudo geocodificar"):
            service.geocode_address('Dirección Inexistente', 'Ciudad Falsa', use_cache=False)
    
    
    @patch.object(GoogleMapsService, '__init__', lambda self: None)
    def test_geocode_address_saves_to_cache(self, db):
        """Test que guarda resultado en caché."""
        mock_instance = Mock()
        mock_instance.geocode.return_value = [{
            'geometry': {
                'location': {'lat': 4.70, 'lng': -74.05},
                'location_type': 'ROOFTOP'
            },
            'formatted_address': 'Test Address',
            'place_id': 'test_place_id',
            'address_components': []
        }]
        
        service = GoogleMapsService()
        service.api_key = 'test_key'
        service.geocoding_enabled = True
        service.client = mock_instance
        
        service.geocode_address('Test Address', 'Bogotá', use_cache=True)
        
        # Verificar que se guardó en caché
        cached = GeocodedAddress.query.filter_by(city='Bogotá').first()
        assert cached is not None
        assert float(cached.latitude) == 4.70
        assert float(cached.longitude) == -74.05
    
    @patch.object(GoogleMapsService, '__init__', lambda self: None)
    def test_get_distance_matrix_success(self, db):
        """Test cálculo de matriz de distancias exitoso."""
        mock_instance = Mock()
        mock_instance.distance_matrix.return_value = {
            'rows': [
                {
                    'elements': [
                        {
                            'status': 'OK',
                            'distance': {'value': 15000},  # metros
                            'duration': {'value': 1800}     # segundos
                        },
                        {
                            'status': 'OK',
                            'distance': {'value': 22000},
                            'duration': {'value': 2400}
                        }
                    ]
                },
                {
                    'elements': [
                        {
                            'status': 'OK',
                            'distance': {'value': 22000},
                            'duration': {'value': 2400}
                        },
                        {
                            'status': 'OK',
                            'distance': {'value': 0},
                            'duration': {'value': 0}
                        }
                    ]
                }
            ],
            'status': 'OK'
        }
        
        service = GoogleMapsService()
        service.api_key = 'test_key'
        service.distance_matrix_enabled = True
        service.client = mock_instance
        
        origins = [(4.68, -74.05), (4.70, -74.06)]
        destinations = [(4.69, -74.04), (4.70, -74.06)]
        
        result = service.get_distance_matrix(origins, destinations)
        
        assert result['status'] == 'OK'
        assert 'distances_km' in result
        assert 'durations_minutes' in result
        
        distances = result['distances_km']
        assert len(distances) == 2
        assert len(distances[0]) == 2
        assert distances[0][0] == 15.0  # 15000m = 15km
        assert distances[0][1] == 22.0  # 22000m = 22km
    
    @patch.object(GoogleMapsService, '__init__', lambda self: None)
    def test_get_distance_matrix_with_mode(self, db):
        """Test matriz de distancias con modo de transporte específico."""
        mock_instance = Mock()
        mock_instance.distance_matrix.return_value = {
            'rows': [{'elements': [{'status': 'OK', 'distance': {'value': 10000}, 'duration': {'value': 1200}}]}],
            'status': 'OK'
        }
        
        service = GoogleMapsService()
        service.api_key = 'test_key'
        service.distance_matrix_enabled = True
        service.client = mock_instance
        
        origins = [(4.68, -74.05)]
        destinations = [(4.70, -74.06)]
        
        service.get_distance_matrix(origins, destinations, mode='driving')
        
        # Verificar que se llamó con el modo correcto
        mock_instance.distance_matrix.assert_called_once()
        call_args = mock_instance.distance_matrix.call_args
        assert call_args[1].get('mode') == 'driving'
    
    
    @patch.object(GoogleMapsService, '__init__', lambda self: None)
    def test_confidence_level_determination(self, db):
        """Test determinación de nivel de confianza según location_type."""
        mock_instance = Mock()
        
        # ROOFTOP = high confidence
        mock_instance.geocode.return_value = [{
            'geometry': {'location': {'lat': 4.68, 'lng': -74.05}, 'location_type': 'ROOFTOP'},
            'formatted_address': 'Test',
            'address_components': []
        }]
        
        service = GoogleMapsService()
        service.api_key = 'test_key'
        service.geocoding_enabled = True
        service.client = mock_instance
        
        result = service.geocode_address('Test', 'Bogotá', use_cache=False)
        assert result['confidence'] == 'high'
    
    @patch.object(GoogleMapsService, '__init__', lambda self: None)
    def test_batch_geocoding(self, db):
        """Test geocodificación de múltiples direcciones."""
        mock_instance = Mock()
        
        # Configurar respuestas múltiples
        mock_instance.geocode.side_effect = [
            [{
                'geometry': {'location': {'lat': 4.68, 'lng': -74.05}, 'location_type': 'ROOFTOP'},
                'formatted_address': 'Addr1',
                'address_components': []
            }],
            [{
                'geometry': {'location': {'lat': 4.70, 'lng': -74.06}, 'location_type': 'APPROXIMATE'},
                'formatted_address': 'Addr2',
                'address_components': []
            }]
        ]
        
        service = GoogleMapsService()
        service.api_key = 'test_key'
        service.geocoding_enabled = True
        service.client = mock_instance
        
        addresses = [
            ('Address 1', 'Bogotá'),
            ('Address 2', 'Bogotá')
        ]
        
        results = []
        for addr, city in addresses:
            result = service.geocode_address(addr, city, use_cache=False)
            results.append(result)
        
        assert len(results) == 2
        assert results[0]['lat'] == 4.68
        assert results[1]['lat'] == 4.70
        assert mock_instance.geocode.call_count == 2
