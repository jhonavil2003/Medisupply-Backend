"""
Cliente HTTP para comunicación con el microservicio sales-service.

Este módulo implementa el patrón Circuit Breaker para manejar
la comunicación inter-servicios de manera resiliente.
"""

import os
import time
import logging
from typing import List, Dict, Optional, Any
from datetime import date, datetime
from enum import Enum
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Estados del Circuit Breaker."""
    CLOSED = "closed"       # Funcionamiento normal
    OPEN = "open"           # Demasiados errores, rechaza requests
    HALF_OPEN = "half_open" # Probando si el servicio se recuperó


class CircuitBreaker:
    """
    Implementación del patrón Circuit Breaker para resiliencia.
    
    Previene cascading failures cuando sales-service está caído.
    
    Estados:
    - CLOSED: Todas las peticiones pasan normalmente
    - OPEN: Rechaza peticiones inmediatamente sin hacer HTTP call
    - HALF_OPEN: Permite una petición de prueba para ver si se recuperó
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = requests.exceptions.RequestException
    ):
        """
        Args:
            failure_threshold: Número de fallos consecutivos antes de abrir circuito
            recovery_timeout: Segundos antes de intentar recuperación (HALF_OPEN)
            expected_exception: Tipo de excepción que cuenta como fallo
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
    
    def call(self, func, *args, **kwargs):
        """
        Ejecuta función con protección de Circuit Breaker.
        
        Raises:
            Exception: Si el circuito está abierto o la función falla
        """
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                logger.info("Circuit breaker entering HALF_OPEN state")
            else:
                raise Exception(
                    f"Circuit breaker is OPEN. "
                    f"Service unavailable. "
                    f"Will retry after {self.recovery_timeout}s"
                )
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        
        except self.expected_exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Verifica si es momento de intentar recuperación."""
        if self.last_failure_time is None:
            return True
        
        elapsed = time.time() - self.last_failure_time
        return elapsed >= self.recovery_timeout
    
    def _on_success(self):
        """Llamado cuando la petición es exitosa."""
        self.failure_count = 0
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
            logger.info("Circuit breaker recovered - state is now CLOSED")
    
    def _on_failure(self):
        """Llamado cuando la petición falla."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.error(
                f"Circuit breaker OPEN after {self.failure_count} failures. "
                f"Will attempt recovery after {self.recovery_timeout}s"
            )


class SalesServiceClient:
    """
    Cliente HTTP para comunicación con sales-service.
    
    Proporciona métodos para:
    - Obtener pedidos confirmados pendientes de rutear
    - Obtener detalles de pedidos específicos
    - Actualizar estado de pedidos
    
    Implementa:
    - Circuit Breaker para resiliencia
    - Retry con exponential backoff
    - Timeout configurable
    - Logging detallado
    """
    
    # URL base del servicio (configurable via env var)
    SALES_SERVICE_URL = os.getenv('SALES_SERVICE_URL', 'http://localhost:3003')
    
    # Timeouts (segundos)
    CONNECTION_TIMEOUT = int(os.getenv('SALES_SERVICE_TIMEOUT', '5'))
    READ_TIMEOUT = int(os.getenv('SALES_SERVICE_READ_TIMEOUT', '30'))
    
    # Circuit Breaker configuración
    CIRCUIT_BREAKER_THRESHOLD = int(os.getenv('CIRCUIT_BREAKER_THRESHOLD', '5'))
    CIRCUIT_BREAKER_TIMEOUT = int(os.getenv('CIRCUIT_BREAKER_TIMEOUT', '60'))
    
    def __init__(self):
        """Inicializa el cliente con session y circuit breaker."""
        self.base_url = self.SALES_SERVICE_URL.rstrip('/')
        self.session = self._create_session()
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=self.CIRCUIT_BREAKER_THRESHOLD,
            recovery_timeout=self.CIRCUIT_BREAKER_TIMEOUT
        )
    
    def _create_session(self) -> requests.Session:
        """
        Crea una sesión HTTP con retry strategy.
        
        Retry en:
        - 500, 502, 503, 504 (server errors)
        - Connection errors
        - Read timeouts
        
        3 reintentos con exponential backoff.
        """
        session = requests.Session()
        
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,  # 1s, 2s, 4s
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST", "PUT"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Hace una petición HTTP con Circuit Breaker protection.
        
        Args:
            method: GET, POST, PUT, DELETE
            endpoint: Ruta del endpoint (ej: '/orders')
            params: Query parameters
            json_data: Body JSON para POST/PUT
        
        Returns:
            Dict con la respuesta JSON
        
        Raises:
            requests.exceptions.RequestException: Error de comunicación
            ValueError: Respuesta no es JSON válido
        """
        url = f"{self.base_url}{endpoint}"
        
        def _execute_request():
            logger.info(f"Making {method} request to {url}")
            
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                timeout=(self.CONNECTION_TIMEOUT, self.READ_TIMEOUT),
                headers={'Content-Type': 'application/json'}
            )
            
            response.raise_for_status()
            
            try:
                return response.json()
            except ValueError as e:
                logger.error(f"Invalid JSON response from {url}: {e}")
                raise
        
        try:
            return self.circuit_breaker.call(_execute_request)
        
        except requests.exceptions.Timeout:
            logger.error(f"Timeout calling {url}")
            raise
        
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error to {url}: {e}")
            raise
        
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error from {url}: {e.response.status_code}")
            raise
        
        except Exception as e:
            logger.error(f"Unexpected error calling {url}: {e}")
            raise
    
    def get_confirmed_orders(
        self,
        distribution_center_id: Optional[int] = None,
        planned_date: Optional[date] = None,
        unrouted_only: bool = True,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Obtiene pedidos confirmados pendientes de asignar a ruta.
        
        Args:
            distribution_center_id: Filtrar por centro de distribución
            planned_date: Fecha planeada de entrega
            unrouted_only: Solo pedidos sin asignar a ruta
            limit: Número máximo de pedidos a retornar
        
        Returns:
            Lista de diccionarios con datos de pedidos:
            [
                {
                    'id': 123,
                    'order_number': 'ORD-001',
                    'customer_id': 45,
                    'customer_name': 'Hospital San Ignacio',
                    'delivery_address': 'Calle 100 # 15-20',
                    'city': 'Bogotá',
                    'department': 'Cundinamarca',
                    'latitude': 4.65,
                    'longitude': -74.10,
                    'clinical_priority': 1,
                    'requires_cold_chain': True,
                    'delivery_time_window_start': '08:00',
                    'delivery_time_window_end': '12:00',
                    'estimated_weight_kg': 15.5,
                    'estimated_volume_m3': 0.25,
                    'total_amount': 1500000.00,
                    'confirmed_at': '2025-11-02T10:30:00',
                    'items_count': 5
                }
            ]
        
        Raises:
            requests.exceptions.RequestException: Error de comunicación
        """
        params = {
            'status': 'confirmed'
        }
        
        if distribution_center_id:
            params['distribution_center_id'] = distribution_center_id
        
        if planned_date:
            params['planned_delivery_date'] = planned_date.isoformat()
        
        if unrouted_only:
            params['is_routed'] = 'false'
        
        if limit:
            params['limit'] = limit
        
        try:
            response = self._make_request('GET', '/orders', params=params)
            
            orders = response.get('orders', [])
            logger.info(f"Retrieved {len(orders)} confirmed orders from sales-service")
            
            return orders
        
        except Exception as e:
            logger.error(f"Failed to get confirmed orders: {e}")
            # Retornar lista vacía en caso de error (fail gracefully)
            return []
    
    def get_order_details(self, order_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene detalle completo de un pedido específico.
        
        Args:
            order_id: ID del pedido
        
        Returns:
            Dict con detalle del pedido o None si no existe
            {
                'id': 123,
                'order_number': 'ORD-001',
                'customer': {...},
                'items': [
                    {
                        'product_sku': 'MED-001',
                        'product_name': 'Paracetamol 500mg',
                        'quantity': 100,
                        'requires_cold_chain': False,
                        'weight_kg': 2.5,
                        'volume_m3': 0.05
                    }
                ],
                'delivery_address': {...},
                'clinical_priority': 2,
                'special_instructions': 'Entregar en farmacia interna'
            }
        
        Raises:
            requests.exceptions.RequestException: Error de comunicación
        """
        try:
            response = self._make_request('GET', f'/orders/{order_id}')
            
            order = response.get('order')
            if order:
                logger.info(f"Retrieved details for order {order_id}")
            else:
                logger.warning(f"Order {order_id} not found")
            
            return order
        
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"Order {order_id} not found")
                return None
            raise
        
        except Exception as e:
            logger.error(f"Failed to get order {order_id} details: {e}")
            return None
    
    def get_orders_by_ids(self, order_ids: List[int]) -> Dict[str, Any]:
        """
        Obtiene detalles completos de múltiples órdenes por sus IDs.
        
        Este método optimiza la comunicación con sales-service al recuperar
        múltiples órdenes en una sola llamada HTTP usando el endpoint batch.
        
        Args:
            order_ids: Lista de IDs de órdenes a recuperar
        
        Returns:
            Dict con:
            {
                'orders': List[Dict],        # Órdenes encontradas con detalles completos
                'total': int,                 # Número de órdenes encontradas
                'not_found': List[int],       # IDs de órdenes no encontradas
                'requested': int              # Número de IDs solicitados
            }
            
            Cada orden incluye:
            {
                'id': 123,
                'order_number': 'ORD-2025-001',
                'customer_id': 45,
                'customer_name': 'Hospital San Ignacio',
                'customer': {
                    'id': 45,
                    'razon_social': 'Hospital San Ignacio',
                    'document': '900123456-1',
                    ...
                },
                'items': [
                    {
                        'product_sku': 'MED-001',
                        'product_name': 'Paracetamol 500mg',
                        'quantity': 100,
                        'weight_kg': 2.5,
                        'volume_m3': 0.05,
                        'requires_cold_chain': False,
                        ...
                    }
                ],
                'delivery_address': 'Calle 100 # 15-20',
                'delivery_city': 'Bogotá',
                'delivery_department': 'Cundinamarca',
                'delivery_latitude': 4.6825,
                'delivery_longitude': -74.0543,
                'clinical_priority': 1,
                'requires_cold_chain': True,
                'estimated_weight_kg': 12.5,
                'estimated_volume_m3': 0.25,
                'status': 'confirmed',
                ...
            }
        
        Raises:
            requests.exceptions.RequestException: Error de comunicación
        
        Example:
            >>> client = get_sales_service_client()
            >>> result = client.get_orders_by_ids([101, 102, 103])
            >>> print(f"Found {result['total']} orders")
            >>> print(f"Not found: {result['not_found']}")
        """
        if not order_ids:
            logger.warning("get_orders_by_ids called with empty order_ids list")
            return {
                'orders': [],
                'total': 0,
                'not_found': [],
                'requested': 0
            }
        
        try:
            logger.info(f"Fetching batch of {len(order_ids)} orders from sales-service")
            
            response = self._make_request(
                'POST',
                '/orders/batch',
                json_data={'order_ids': order_ids}
            )
            
            orders = response.get('orders', [])
            not_found = response.get('not_found', [])
            total = response.get('total', len(orders))
            requested = response.get('requested', len(order_ids))
            
            if not_found:
                logger.warning(f"Orders not found: {not_found}")
            
            logger.info(
                f"Batch retrieval complete: {total} found, "
                f"{len(not_found)} not found out of {requested} requested"
            )
            
            return {
                'orders': orders,
                'total': total,
                'not_found': not_found,
                'requested': requested
            }
        
        except Exception as e:
            logger.error(f"Failed to get orders by IDs: {e}")
            # Retornar estructura vacía en caso de error (fail gracefully)
            return {
                'orders': [],
                'total': 0,
                'not_found': order_ids,  # Marcar todos como no encontrados
                'requested': len(order_ids)
            }
    
    def update_order_status(
        self,
        order_id: int,
        new_status: str,
        notes: Optional[str] = None
    ) -> bool:
        """
        Actualiza el estado de un pedido.
        
        Transiciones comunes:
        - confirmed → processing (al asignar a ruta)
        - processing → in_transit (cuando ruta inicia)
        - in_transit → delivered (al completar entrega)
        
        Args:
            order_id: ID del pedido
            new_status: Nuevo estado (confirmed, processing, in_transit, delivered, cancelled)
            notes: Notas adicionales sobre el cambio
        
        Returns:
            True si actualización fue exitosa, False en caso contrario
        
        Raises:
            requests.exceptions.RequestException: Error de comunicación
        """
        json_data = {
            'status': new_status
        }
        
        if notes:
            json_data['notes'] = notes
        
        try:
            # Usar PATCH /orders/{id} en lugar de PUT /orders/{id}/status
            response = self._make_request(
                'PATCH',
                f'/orders/{order_id}',
                json_data=json_data
            )
            
            # La respuesta es el objeto order actualizado
            if response and response.get('id') == order_id:
                logger.info(f"✅ Updated order {order_id} status to {new_status}")
                return True
            else:
                logger.warning(f"⚠️ Failed to update order {order_id} status")
                return False
        
        except Exception as e:
            logger.error(f"❌ Failed to update order {order_id} status: {e}")
            return False
    
    def mark_orders_as_routed(
        self,
        order_ids: List[int],
        route_id: int
    ) -> Dict[str, Any]:
        """
        Marca múltiples pedidos como asignados a una ruta.
        
        Args:
            order_ids: Lista de IDs de pedidos
            route_id: ID de la ruta asignada
        
        Returns:
            Dict con resultado:
            {
                'success': True,
                'updated_count': 5,
                'failed_orders': []
            }
        """
        results = {
            'success': True,
            'updated_count': 0,
            'failed_orders': []
        }
        
        for order_id in order_ids:
            try:
                json_data = {
                    'is_routed': True,
                    'route_id': route_id,
                    'routed_at': datetime.utcnow().isoformat()
                }
                
                response = self._make_request(
                    'PUT',
                    f'/orders/{order_id}',
                    json_data=json_data
                )
                
                if response.get('status') == 'success':
                    results['updated_count'] += 1
                else:
                    results['failed_orders'].append(order_id)
            
            except Exception as e:
                logger.error(f"Failed to mark order {order_id} as routed: {e}")
                results['failed_orders'].append(order_id)
                results['success'] = False
        
        logger.info(
            f"Marked {results['updated_count']}/{len(order_ids)} orders as routed. "
            f"Route ID: {route_id}"
        )
        
        return results
    
    def get_order_statistics(
        self,
        distribution_center_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Obtiene estadísticas de pedidos para análisis.
        
        Args:
            distribution_center_id: Filtrar por centro de distribución
            start_date: Fecha inicio del rango
            end_date: Fecha fin del rango
        
        Returns:
            Dict con estadísticas:
            {
                'total_orders': 150,
                'confirmed_orders': 25,
                'unrouted_orders': 15,
                'cold_chain_orders': 8,
                'high_priority_orders': 5,
                'avg_weight_kg': 12.5,
                'avg_volume_m3': 0.35
            }
        """
        params = {}
        
        if distribution_center_id:
            params['distribution_center_id'] = distribution_center_id
        
        if start_date:
            params['start_date'] = start_date.isoformat()
        
        if end_date:
            params['end_date'] = end_date.isoformat()
        
        try:
            response = self._make_request('GET', '/orders/statistics', params=params)
            return response.get('statistics', {})
        
        except Exception as e:
            logger.error(f"Failed to get order statistics: {e}")
            return {}
    
    def health_check(self) -> bool:
        """
        Verifica si sales-service está disponible.
        
        Returns:
            True si el servicio responde, False en caso contrario
        """
        try:
            response = self._make_request('GET', '/health')
            is_healthy = response.get('status') == 'healthy'
            
            if is_healthy:
                logger.info("Sales service is healthy")
            else:
                logger.warning("Sales service health check failed")
            
            return is_healthy
        
        except Exception as e:
            logger.error(f"Sales service health check failed: {e}")
            return False

    def get_customers_by_ids(self, customer_ids: List[int]) -> Dict[str, Any]:
        """
        Obtiene datos de múltiples clientes por sus IDs (batch request).
        
        Útil para generar rutas de visitas con información completa de clientes.
        
        Args:
            customer_ids: Lista de IDs de clientes a obtener
        
        Returns:
            Dict con:
            {
                'customers': [
                    {
                        'id': 1,
                        'business_name': 'Farmacia San Rafael',
                        'document_type': 'NIT',
                        'document_number': '900123456-1',
                        'customer_type': 'farmacia',
                        'address': 'Calle 50 #20-30',
                        'neighborhood': 'Chapinero',
                        'city': 'Bogota',
                        'department': 'Cundinamarca',
                        'latitude': 4.6486259,
                        'longitude': -74.0628451,
                        'contact_name': 'Juan Perez',
                        'contact_phone': '3001234567',
                        'contact_email': 'juan.perez@sanrafael.com',
                        'salesperson_id': 2,
                        'is_active': True
                    }
                ],
                'total': 1,
                'not_found': [],
                'requested': 1
            }
        
        Raises:
            requests.exceptions.RequestException: Error de comunicación
        
        Example:
            >>> client = get_sales_service_client()
            >>> result = client.get_customers_by_ids([1, 5, 12])
            >>> print(f"Found {result['total']} customers")
            >>> for customer in result['customers']:
            >>>     print(f"  - {customer['business_name']}: {customer['latitude']}, {customer['longitude']}")
        """
        if not customer_ids:
            logger.warning("get_customers_by_ids called with empty customer_ids list")
            return {
                'customers': [],
                'total': 0,
                'not_found': [],
                'requested': 0
            }
        
        try:
            logger.info(f"Fetching batch of {len(customer_ids)} customers from sales-service")
            
            response = self._make_request(
                'POST',
                '/customers/batch',
                json_data={'customer_ids': customer_ids}
            )
            
            customers = response.get('customers', [])
            not_found = response.get('not_found', [])
            total = response.get('total', len(customers))
            
            logger.info(
                f"Retrieved {total} customers from sales-service "
                f"({len(not_found)} not found)"
            )
            
            return {
                'customers': customers,
                'total': total,
                'not_found': not_found,
                'requested': len(customer_ids)
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch customers from sales-service: {e}")
            raise


# Instancia singleton del cliente
_client_instance = None


def get_sales_service_client() -> SalesServiceClient:
    """
    Retorna instancia singleton del cliente.
    
    Uso:
        from src.services.sales_service_client import get_sales_service_client
        
        client = get_sales_service_client()
        orders = client.get_confirmed_orders(distribution_center_id=1)
    """
    global _client_instance
    
    if _client_instance is None:
        _client_instance = SalesServiceClient()
    
    return _client_instance
