#!/usr/bin/env python3
"""
Script de prueba E2E simple para validar POST /orders desde dentro del contenedor
Este script se ejecuta dentro del contenedor de sales-service para probar la integración
"""
import requests
import json
import sys

def test_create_order():
    """Prueba la creación de un pedido validando producto y stock"""
    
    url = "http://localhost:3003/orders"
    
    order_data = {
        "customer_id": 1,  # Hospital San Ignacio
        "seller_id": "SELLER001",
        "items": [
            {
                "product_sku": "JER-001",
                "quantity": 5,
                "discount_percentage": 0
            }
        ],
        "payment_terms": "60_dias",
        "preferred_distribution_center": "BOG-01"
    }
    
    print("="*70)
    print("🧪 PRUEBA E2E - POST /orders con validación de stock")
    print("="*70)
    print(f"\n📋 Datos del pedido:")
    print(json.dumps(order_data, indent=2))
    
    try:
        print(f"\n🚀 Enviando solicitud a {url}...")
        response = requests.post(url, json=order_data, timeout=5)
        
        print(f"\n📊 Respuesta HTTP: {response.status_code}")
        print(f"📄 Contenido:")
        print(json.dumps(response.json(), indent=2))
        
        if response.status_code == 201:
            print("\n✅ ÉXITO: Pedido creado correctamente")
            order = response.json()
            print(f"\n📋 Resumen del pedido:")
            print(f"  - Número de orden: {order['order_number']}")
            print(f"  - Cliente: {order['customer']['business_name']}")
            print(f"  - Total: ${order['total_amount']:,.2f}")
            print(f"  - Items: {len(order['items'])}")
            for item in order['items']:
                print(f"    * {item['product_name']} - Qty: {item['quantity']} - Stock confirmado: {item['stock_confirmed']}")
            return 0
        else:
            print(f"\n❌ ERROR: {response.status_code}")
            return 1
            
    except requests.exceptions.Timeout:
        print("\n❌ ERROR: Timeout - La solicitud tardó más de 5 segundos")
        return 1
    except requests.exceptions.ConnectionError as e:
        print(f"\n❌ ERROR de conexión: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR inesperado: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(test_create_order())
