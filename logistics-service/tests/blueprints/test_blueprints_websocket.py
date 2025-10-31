import pytest

def test_websocket_health(client):
    response = client.get('/websocket/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'
    assert 'endpoint' in data
    assert 'message' in data

def test_websocket_test_notification(client):
    payload = {
        "product_sku": "TEST-001",
        "change_type": "test",
        "old_quantity": 0,
        "new_quantity": 100,
        "location": "Zona A-01"
    }
    response = client.post('/websocket/test-notification', json=payload)
    assert response.status_code == 200
    data = response.get_json()
    # El endpoint retorna 'notification_sent' y 'message', no 'success'
    assert data['status'] == 'success'
    assert 'message' in data
