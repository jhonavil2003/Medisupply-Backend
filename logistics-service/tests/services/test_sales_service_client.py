"""
Tests unitarios para services/sales_service_client.py

Coverage objetivo: >90%

Funcionalidad a probar:
- CircuitBreaker (estados y transiciones)
- SalesServiceClient (métodos HTTP)
- Manejo de errores y timeouts
- Retry logic
- Health checks
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import date, datetime
import requests
from requests.exceptions import Timeout, ConnectionError, HTTPError
import time

from src.services.sales_service_client import (
    CircuitState,
    CircuitBreaker,
    SalesServiceClient,
    get_sales_service_client
)


class TestCircuitBreaker:
    """Tests para el Circuit Breaker pattern"""

    def test_init_default_values(self):
        """Test: Inicialización con valores por defecto"""
        cb = CircuitBreaker()
        
        assert cb.failure_threshold == 5
        assert cb.recovery_timeout == 60
        assert cb.expected_exception == requests.exceptions.RequestException
        assert cb.failure_count == 0
        assert cb.last_failure_time is None
        assert cb.state == CircuitState.CLOSED

    def test_init_custom_values(self):
        """Test: Inicialización con valores custom"""
        cb = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=30,
            expected_exception=ValueError
        )
        
        assert cb.failure_threshold == 3
        assert cb.recovery_timeout == 30
        assert cb.expected_exception == ValueError

    def test_call_success_when_closed(self):
        """Test: Llamada exitosa cuando circuito está cerrado"""
        cb = CircuitBreaker()
        
        mock_func = Mock(return_value="success")
        result = cb.call(mock_func, "arg1", kwarg1="value1")
        
        assert result == "success"
        mock_func.assert_called_once_with("arg1", kwarg1="value1")
        assert cb.failure_count == 0
        assert cb.state == CircuitState.CLOSED

    def test_call_failure_increments_count(self):
        """Test: Fallo incrementa contador"""
        cb = CircuitBreaker(failure_threshold=3)
        
        mock_func = Mock(side_effect=requests.exceptions.RequestException("Error"))
        
        with pytest.raises(requests.exceptions.RequestException):
            cb.call(mock_func)
        
        assert cb.failure_count == 1
        assert cb.last_failure_time is not None
        assert cb.state == CircuitState.CLOSED  # Todavía no alcanza threshold

    def test_circuit_opens_after_threshold(self):
        """Test: Circuito se abre después de alcanzar threshold"""
        cb = CircuitBreaker(failure_threshold=3)
        
        mock_func = Mock(side_effect=requests.exceptions.RequestException("Error"))
        
        # Fallar 3 veces
        for i in range(3):
            with pytest.raises(requests.exceptions.RequestException):
                cb.call(mock_func)
        
        assert cb.failure_count == 3
        assert cb.state == CircuitState.OPEN

    def test_circuit_open_rejects_calls(self):
        """Test: Circuito abierto rechaza llamadas sin ejecutarlas"""
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=100)
        
        mock_func = Mock(side_effect=requests.exceptions.RequestException("Error"))
        
        # Abrir circuito
        for _ in range(2):
            with pytest.raises(requests.exceptions.RequestException):
                cb.call(mock_func)
        
        assert cb.state == CircuitState.OPEN
        
        # Intentar llamar con circuito abierto
        mock_func_2 = Mock(return_value="success")
        
        with pytest.raises(Exception) as exc_info:
            cb.call(mock_func_2)
        
        assert "Circuit breaker is OPEN" in str(exc_info.value)
        # No se ejecutó la función
        mock_func_2.assert_not_called()

    def test_circuit_transitions_to_half_open_after_timeout(self):
        """Test: Circuito pasa a HALF_OPEN después del timeout"""
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=1)
        
        mock_func = Mock(side_effect=requests.exceptions.RequestException("Error"))
        
        # Abrir circuito
        for _ in range(2):
            with pytest.raises(requests.exceptions.RequestException):
                cb.call(mock_func)
        
        assert cb.state == CircuitState.OPEN
        
        # Esperar timeout
        time.sleep(1.1)
        
        # Siguiente llamada debe poner en HALF_OPEN
        mock_func_2 = Mock(return_value="success")
        result = cb.call(mock_func_2)
        
        assert result == "success"
        assert cb.state == CircuitState.CLOSED  # Se recuperó

    def test_circuit_closes_from_half_open_on_success(self):
        """Test: HALF_OPEN → CLOSED en éxito"""
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=1)
        
        # Abrir circuito
        mock_func_fail = Mock(side_effect=requests.exceptions.RequestException("Error"))
        for _ in range(2):
            with pytest.raises(requests.exceptions.RequestException):
                cb.call(mock_func_fail)
        
        assert cb.state == CircuitState.OPEN
        
        # Esperar y recuperar
        time.sleep(1.1)
        
        mock_func_success = Mock(return_value="recovered")
        result = cb.call(mock_func_success)
        
        assert result == "recovered"
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0

    def test_circuit_reopens_from_half_open_on_failure(self):
        """Test: HALF_OPEN → OPEN en fallo"""
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=1)
        
        # Abrir circuito
        mock_func_fail = Mock(side_effect=requests.exceptions.RequestException("Error"))
        with pytest.raises(requests.exceptions.RequestException):
            cb.call(mock_func_fail)
        
        assert cb.state == CircuitState.OPEN
        
        # Esperar timeout
        time.sleep(1.1)
        
        # Fallar nuevamente
        with pytest.raises(requests.exceptions.RequestException):
            cb.call(mock_func_fail)
        
        assert cb.state == CircuitState.OPEN

    def test_should_attempt_reset_no_failure(self):
        """Test: _should_attempt_reset cuando no hay fallos previos"""
        cb = CircuitBreaker()
        assert cb._should_attempt_reset() is True

    def test_should_attempt_reset_timeout_elapsed(self):
        """Test: _should_attempt_reset cuando pasó el timeout"""
        cb = CircuitBreaker(recovery_timeout=1)
        cb.last_failure_time = time.time() - 2  # Hace 2 segundos
        
        assert cb._should_attempt_reset() is True

    def test_should_attempt_reset_timeout_not_elapsed(self):
        """Test: _should_attempt_reset cuando NO pasó el timeout"""
        cb = CircuitBreaker(recovery_timeout=100)
        cb.last_failure_time = time.time()  # Ahora
        
        assert cb._should_attempt_reset() is False


class TestSalesServiceClientInit:
    """Tests de inicialización del cliente"""

    @patch.dict('os.environ', {
        'SALES_SERVICE_URL': 'http://test-service:8080',
        'SALES_SERVICE_TIMEOUT': '10',
        'CIRCUIT_BREAKER_TIMEOUT': '30',
        'CIRCUIT_BREAKER_THRESHOLD': '3'
    })
    def test_init_with_env_vars(self):
        """Test: Inicialización con variables de entorno"""
        # Reimportar módulo para que tome las nuevas env vars
        import importlib
        from src.services import sales_service_client
        importlib.reload(sales_service_client)
        
        client = sales_service_client.SalesServiceClient()
        
        assert client.base_url == 'http://test-service:8080'
        assert client.CONNECTION_TIMEOUT == 10
        assert client.circuit_breaker.failure_threshold == 3
        assert client.circuit_breaker.recovery_timeout == 30

    def test_init_default_values(self):
        """Test: Inicialización con valores por defecto"""
        client = SalesServiceClient()
        
        assert 'localhost' in client.base_url or 'SALES_SERVICE_URL' in client.base_url
        assert isinstance(client.session, requests.Session)
        # CircuitBreaker es de este módulo
        assert client.circuit_breaker.__class__.__name__ == 'CircuitBreaker'

    def test_create_session_has_retry_strategy(self):
        """Test: Session tiene configuración de retry"""
        client = SalesServiceClient()
        session = client.session
        
        # Verificar que tiene adaptadores montados
        assert 'http://' in session.adapters
        assert 'https://' in session.adapters


def _create_mock_response(json_data, status_code=200):
    """Helper para crear respuesta HTTP mockeada"""
    mock_resp = Mock()
    mock_resp.status_code = status_code
    mock_resp.json.return_value = json_data
    mock_resp.raise_for_status = Mock()
    return mock_resp


class TestSalesServiceClientRequests:
    """Tests de métodos HTTP del cliente"""

    def test_get_confirmed_orders_success(self):
        """Test: get_confirmed_orders exitoso"""
        client = SalesServiceClient()
        
        mock_response = _create_mock_response({
            'orders': [
                {'id': 101, 'order_number': 'ORD-101', 'customer_name': 'Cliente 1'},
                {'id': 102, 'order_number': 'ORD-102', 'customer_name': 'Cliente 2'}
            ]
        })
        client.session.request = Mock(return_value=mock_response)
        
        orders = client.get_confirmed_orders(
            distribution_center_id=1,
            planned_date=date(2025, 11, 20),
            unrouted_only=True,
            limit=10
        )
        
        assert len(orders) == 2
        assert orders[0]['id'] == 101
        
        # Verificar parámetros
        call_args = client.session.request.call_args
        assert call_args[1]['params']['status'] == 'confirmed'

    def test_get_confirmed_orders_error_returns_empty(self):
        """Test: get_confirmed_orders retorna [] en error"""
        client = SalesServiceClient()
        client.session.request = Mock(side_effect=ConnectionError("Network error"))
        
        orders = client.get_confirmed_orders()
        assert orders == []

    def test_get_order_details_success(self):
        """Test: get_order_details exitoso"""
        client = SalesServiceClient()
        
        mock_response = _create_mock_response({
            'order': {
                'id': 101,
                'order_number': 'ORD-101',
                'items': [{'product_sku': 'MED-001', 'quantity': 10}]
            }
        })
        client.session.request = Mock(return_value=mock_response)
        
        order = client.get_order_details(101)
        
        assert order is not None
        assert order['id'] == 101
        assert len(order['items']) == 1

    def test_get_order_details_not_found(self):
        """Test: get_order_details con orden no encontrada"""
        client = SalesServiceClient()
        
        http_error = HTTPError("404 Not Found")
        http_error.response = Mock(status_code=404)
        
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status = Mock(side_effect=http_error)
        
        client.session.request = Mock(return_value=mock_response)
        
        order = client.get_order_details(999)
        assert order is None

    def test_get_orders_by_ids_success(self):
        """Test: get_orders_by_ids exitoso"""
        client = SalesServiceClient()
        
        mock_response = _create_mock_response({
            'orders': [
                {'id': 101, 'order_number': 'ORD-101'},
                {'id': 102, 'order_number': 'ORD-102'}
            ],
            'total': 2,
            'not_found': [103],
            'requested': 3
        })
        client.session.request = Mock(return_value=mock_response)
        
        result = client.get_orders_by_ids([101, 102, 103])
        
        assert result['total'] == 2
        assert len(result['orders']) == 2
        assert result['not_found'] == [103]

    def test_get_orders_by_ids_empty_list(self):
        """Test: get_orders_by_ids con lista vacía"""
        client = SalesServiceClient()
        client.session.request = Mock()
        
        result = client.get_orders_by_ids([])
        
        assert result['orders'] == []
        assert result['total'] == 0
        client.session.request.assert_not_called()

    def test_get_orders_by_ids_error_marks_all_not_found(self):
        """Test: get_orders_by_ids en error marca todos como not_found"""
        client = SalesServiceClient()
        client.session.request = Mock(side_effect=Timeout("Timeout"))
        
        result = client.get_orders_by_ids([101, 102])
        
        assert result['total'] == 0
        assert set(result['not_found']) == {101, 102}

    def test_update_order_status_success(self):
        """Test: update_order_status exitoso"""
        client = SalesServiceClient()
        
        mock_response = _create_mock_response({'id': 101, 'status': 'processing'})
        client.session.request = Mock(return_value=mock_response)
        
        success = client.update_order_status(101, 'processing', notes='Assigned to route')
        assert success is True

    def test_update_order_status_failure(self):
        """Test: update_order_status falla"""
        client = SalesServiceClient()
        
        http_error = HTTPError("500 Server Error")
        http_error.response = Mock(status_code=500)
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status = Mock(side_effect=http_error)
        
        client.session.request = Mock(return_value=mock_response)
        
        success = client.update_order_status(101, 'processing')
        assert success is False

    def test_mark_orders_as_routed_success(self):
        """Test: mark_orders_as_routed exitoso"""
        client = SalesServiceClient()
        
        mock_response = _create_mock_response({'status': 'success'})
        client.session.request = Mock(return_value=mock_response)
        
        result = client.mark_orders_as_routed([101, 102], route_id=5)
        
        assert result['success'] is True
        assert result['updated_count'] == 2
        assert result['failed_orders'] == []

    def test_mark_orders_as_routed_partial_failure(self):
        """Test: mark_orders_as_routed con fallo parcial"""
        client = SalesServiceClient()
        
        # Primera llamada exitosa, segunda falla
        http_error = HTTPError("500 Server Error")
        http_error.response = Mock(status_code=500)
        mock_fail_response = Mock()
        mock_fail_response.status_code = 500
        mock_fail_response.raise_for_status = Mock(side_effect=http_error)
        
        client.session.request = Mock(side_effect=[
            _create_mock_response({'status': 'success'}),
            mock_fail_response
        ])
        
        result = client.mark_orders_as_routed([101, 102], route_id=5)
        
        assert result['success'] is False
        assert result['updated_count'] == 1
        assert 102 in result['failed_orders']

    def test_get_order_statistics_success(self):
        """Test: get_order_statistics exitoso"""
        client = SalesServiceClient()
        
        mock_response = _create_mock_response({
            'statistics': {
                'total_orders': 150,
                'confirmed_orders': 25,
                'avg_weight_kg': 12.5
            }
        })
        client.session.request = Mock(return_value=mock_response)
        
        stats = client.get_order_statistics(
            distribution_center_id=1,
            start_date=date(2025, 11, 1),
            end_date=date(2025, 11, 30)
        )
        
        assert stats['total_orders'] == 150
        assert stats['confirmed_orders'] == 25

    def test_health_check_healthy(self):
        """Test: health_check cuando servicio está sano"""
        client = SalesServiceClient()
        
        mock_response = _create_mock_response({'status': 'healthy'})
        client.session.request = Mock(return_value=mock_response)
        
        is_healthy = client.health_check()
        assert is_healthy is True

    def test_health_check_unhealthy(self):
        """Test: health_check cuando servicio no responde"""
        client = SalesServiceClient()
        client.session.request = Mock(side_effect=ConnectionError("Connection refused"))
        
        is_healthy = client.health_check()
        assert is_healthy is False

    def test_get_customers_by_ids_success(self):
        """Test: get_customers_by_ids exitoso"""
        client = SalesServiceClient()
        
        mock_response = _create_mock_response({
            'customers': [
                {'id': 1, 'business_name': 'Farmacia San Rafael'},
                {'id': 5, 'business_name': 'Hospital Central'}
            ],
            'total': 2,
            'not_found': [12]
        })
        client.session.request = Mock(return_value=mock_response)
        
        result = client.get_customers_by_ids([1, 5, 12])
        
        assert result['total'] == 2
        assert len(result['customers']) == 2
        assert result['not_found'] == [12]

    def test_get_customers_by_ids_empty_list(self):
        """Test: get_customers_by_ids con lista vacía"""
        client = SalesServiceClient()
        client.session.request = Mock()
        
        result = client.get_customers_by_ids([])
        
        assert result['customers'] == []
        assert result['total'] == 0
        client.session.request.assert_not_called()

    def test_get_customers_by_ids_error_raises(self):
        """Test: get_customers_by_ids propaga excepción en error"""
        client = SalesServiceClient()
        client.session.request = Mock(side_effect=ConnectionError("Network error"))
        
        with pytest.raises(ConnectionError):
            client.get_customers_by_ids([1, 2, 3])


class TestSalesServiceClientMakeRequest:
    """Tests del método _make_request"""

    def test_make_request_get_success(self):
        """Test: _make_request GET exitoso"""
        client = SalesServiceClient()
        
        mock_response = _create_mock_response({'data': 'test'})
        client.session.request = Mock(return_value=mock_response)
        
        result = client._make_request('GET', '/test', params={'key': 'value'})
        
        assert result == {'data': 'test'}
        client.session.request.assert_called_once()

    def test_make_request_post_with_json(self):
        """Test: _make_request POST con JSON body"""
        client = SalesServiceClient()
        
        mock_response = _create_mock_response({'success': True})
        client.session.request = Mock(return_value=mock_response)
        
        result = client._make_request('POST', '/create', json_data={'name': 'test'})
        
        assert result == {'success': True}

    def test_make_request_timeout_raises(self):
        """Test: _make_request propaga Timeout"""
        client = SalesServiceClient()
        client.session.request = Mock(side_effect=Timeout("Timeout"))
        
        with pytest.raises(Timeout):
            client._make_request('GET', '/test')

    def test_make_request_connection_error_raises(self):
        """Test: _make_request propaga ConnectionError"""
        client = SalesServiceClient()
        client.session.request = Mock(side_effect=ConnectionError("Connection refused"))
        
        with pytest.raises(ConnectionError):
            client._make_request('GET', '/test')

    def test_make_request_http_error_raises(self):
        """Test: _make_request propaga HTTPError"""
        client = SalesServiceClient()
        
        http_error = HTTPError("500 Server Error")
        http_error.response = Mock(status_code=500)
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status = Mock(side_effect=http_error)
        
        client.session.request = Mock(return_value=mock_response)
        
        with pytest.raises(HTTPError):
            client._make_request('GET', '/test')

    def test_make_request_invalid_json_raises(self):
        """Test: _make_request con respuesta JSON inválida"""
        client = SalesServiceClient()
        
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json = Mock(side_effect=ValueError("Invalid JSON"))
        
        client.session.request = Mock(return_value=mock_response)
        
        with pytest.raises(ValueError):
            client._make_request('GET', '/test')


class TestGetSalesServiceClient:
    """Tests del singleton factory"""

    def test_get_sales_service_client_returns_instance(self):
        """Test: get_sales_service_client retorna instancia"""
        client = get_sales_service_client()
        assert client.__class__.__name__ == 'SalesServiceClient'

    def test_get_sales_service_client_singleton(self):
        """Test: get_sales_service_client retorna misma instancia"""
        client1 = get_sales_service_client()
        client2 = get_sales_service_client()
        
        assert client1 is client2


class TestIntegration:
    """Tests de integración entre CircuitBreaker y SalesServiceClient"""

    def test_circuit_breaker_integration(self):
        """Test: Circuit breaker se activa después de múltiples fallos"""
        client = SalesServiceClient()
        client.session.request = Mock(side_effect=ConnectionError("Network error"))
        client.circuit_breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=100)
        
        # Primer fallo
        with pytest.raises(ConnectionError):
            client._make_request('GET', '/test')
        
        # Verificar estado y contador
        assert client.circuit_breaker.state.value == 'closed'
        assert client.circuit_breaker.failure_count == 1
        
        # Segundo fallo - abre circuito
        with pytest.raises(ConnectionError):
            client._make_request('GET', '/test')
        
        # Verificar circuito abierto
        assert client.circuit_breaker.state.value == 'open'
        assert client.circuit_breaker.failure_count == 2
        
        # Tercer intento - rechazado sin hacer HTTP call
        with pytest.raises(Exception) as exc_info:
            client._make_request('GET', '/test')
        
        assert "Circuit breaker is OPEN" in str(exc_info.value)
