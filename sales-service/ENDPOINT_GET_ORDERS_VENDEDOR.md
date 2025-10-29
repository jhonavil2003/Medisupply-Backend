# Endpoint GET /orders - Obtener Órdenes por Vendedor

## Descripción General

Este documento detalla el funcionamiento del endpoint `GET /orders` del microservicio **sales-service**, con especial énfasis en su uso para obtener el listado de órdenes filtradas por vendedor (`seller_id`).

## Información del Endpoint

- **URL**: `http://localhost:3003/orders`
- **Método HTTP**: `GET`
- **Autenticación**: No especificada en la implementación actual
- **Content-Type**: `application/json`

---

## Request (Solicitud)

### Query Parameters (Parámetros de Consulta)

El endpoint acepta los siguientes parámetros opcionales en la URL como query strings:

| Parámetro | Tipo | Requerido | Descripción | Ejemplo |
|-----------|------|-----------|-------------|---------|
| `seller_id` | string | No | ID del vendedor para filtrar órdenes | `SELLER-001` |
| `customer_id` | integer | No | ID del cliente para filtrar órdenes | `1` |
| `status` | string | No | Estado de la orden para filtrar | `pending`, `confirmed`, `processing`, `shipped`, `delivered`, `cancelled` |

### Ejemplos de Request

#### 1. Obtener todas las órdenes de un vendedor específico

```bash
GET /orders?seller_id=SELLER-001
```

```bash
curl "http://localhost:3003/orders?seller_id=SELLER-001"
```

#### 2. Obtener órdenes pendientes de un vendedor

```bash
GET /orders?seller_id=SELLER-001&status=pending
```

```bash
curl "http://localhost:3003/orders?seller_id=SELLER-001&status=pending"
```

#### 3. Obtener órdenes de un vendedor para un cliente específico

```bash
GET /orders?seller_id=SELLER-001&customer_id=5
```

```bash
curl "http://localhost:3003/orders?seller_id=SELLER-001&customer_id=5"
```

#### 4. Obtener todas las órdenes (sin filtros)

```bash
GET /orders
```

```bash
curl "http://localhost:3003/orders"
```

### Headers de Request

```
Accept: application/json
```

---

## Response (Respuesta)

### Respuesta Exitosa (200 OK)

#### Estructura del Response Body

```json
{
  "orders": [
    {
      "id": integer,
      "order_number": string,
      "customer_id": integer,
      "seller_id": string,
      "seller_name": string,
      "order_date": string (ISO 8601),
      "status": string,
      "subtotal": float,
      "discount_amount": float,
      "tax_amount": float,
      "total_amount": float,
      "payment_terms": string,
      "payment_method": string,
      "delivery_address": string,
      "delivery_city": string,
      "delivery_department": string,
      "preferred_distribution_center": string,
      "notes": string,
      "created_at": string (ISO 8601),
      "updated_at": string (ISO 8601),
      "items": [
        {
          "id": integer,
          "order_id": integer,
          "product_sku": string,
          "product_name": string,
          "quantity": integer,
          "unit_price": float,
          "discount_percentage": float,
          "discount_amount": float,
          "tax_percentage": float,
          "tax_amount": float,
          "subtotal": float,
          "total": float,
          "distribution_center_code": string,
          "stock_confirmed": boolean,
          "stock_confirmation_date": string (ISO 8601),
          "created_at": string (ISO 8601)
        }
      ]
    }
  ],
  "total": integer
}
```

#### Descripción de Campos de Response

**Campos de la Orden (Order)**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | integer | Identificador único de la orden |
| `order_number` | string | Número de orden único (formato: ORD-YYYYMMDD-0001) |
| `customer_id` | integer | ID del cliente que realiza la orden |
| `seller_id` | string | ID del vendedor que registró la orden |
| `seller_name` | string | Nombre completo del vendedor |
| `order_date` | string | Fecha y hora de creación de la orden (formato ISO 8601) |
| `status` | string | Estado actual de la orden: `pending`, `confirmed`, `processing`, `shipped`, `delivered`, `cancelled` |
| `subtotal` | float | Suma de los subtotales de todos los ítems (antes de impuestos) |
| `discount_amount` | float | Monto total de descuentos aplicados a la orden |
| `tax_amount` | float | Monto total de impuestos (IVA) de la orden |
| `total_amount` | float | Monto total de la orden (subtotal + impuestos - descuentos) |
| `payment_terms` | string | Términos de pago: `contado`, `credito_30`, `credito_60`, `credito_90` |
| `payment_method` | string | Método de pago: `transferencia`, `cheque`, `efectivo` |
| `delivery_address` | string | Dirección de entrega |
| `delivery_city` | string | Ciudad de entrega |
| `delivery_department` | string | Departamento/Estado de entrega |
| `preferred_distribution_center` | string | Código del centro de distribución preferido |
| `notes` | string | Notas adicionales de la orden |
| `created_at` | string | Fecha de creación del registro (formato ISO 8601) |
| `updated_at` | string | Fecha de última actualización del registro (formato ISO 8601) |
| `items` | array | Lista de ítems/productos de la orden |

**Campos de los Ítems de la Orden (Order Items)**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | integer | Identificador único del ítem |
| `order_id` | integer | ID de la orden a la que pertenece |
| `product_sku` | string | SKU (código) del producto |
| `product_name` | string | Nombre del producto |
| `quantity` | integer | Cantidad solicitada del producto |
| `unit_price` | float | Precio unitario del producto |
| `discount_percentage` | float | Porcentaje de descuento aplicado (0-100) |
| `discount_amount` | float | Monto del descuento calculado |
| `tax_percentage` | float | Porcentaje de impuesto (IVA) - Por defecto 19% en Colombia |
| `tax_amount` | float | Monto del impuesto calculado |
| `subtotal` | float | Subtotal del ítem (precio × cantidad - descuento) |
| `total` | float | Total del ítem (subtotal + impuestos) |
| `distribution_center_code` | string | Código del centro de distribución desde donde se enviará |
| `stock_confirmed` | boolean | Indica si el stock fue confirmado para este ítem |
| `stock_confirmation_date` | string | Fecha de confirmación del stock (formato ISO 8601) |
| `created_at` | string | Fecha de creación del ítem (formato ISO 8601) |

**Campo Resumen**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `total` | integer | Número total de órdenes retornadas por la consulta |

### Ejemplo de Respuesta Exitosa

```json
{
  "orders": [
    {
      "id": 1,
      "order_number": "ORD-20251016-0001",
      "customer_id": 1,
      "seller_id": "SELLER-001",
      "seller_name": "Juan Pérez",
      "order_date": "2025-10-16T14:30:00",
      "status": "pending",
      "subtotal": 10500.00,
      "discount_amount": 525.00,
      "tax_amount": 1895.25,
      "total_amount": 11870.25,
      "payment_terms": "credito_30",
      "payment_method": "transferencia",
      "delivery_address": "Calle 123 #45-67",
      "delivery_city": "Bogotá",
      "delivery_department": "Cundinamarca",
      "preferred_distribution_center": "DC-BOG-001",
      "notes": "Entrega urgente",
      "created_at": "2025-10-16T14:30:00",
      "updated_at": "2025-10-16T14:30:00",
      "items": [
        {
          "id": 1,
          "order_id": 1,
          "product_sku": "JER-001",
          "product_name": "Jeringa desechable 3ml",
          "quantity": 10,
          "unit_price": 350.00,
          "discount_percentage": 5.00,
          "discount_amount": 175.00,
          "tax_percentage": 19.00,
          "tax_amount": 631.25,
          "subtotal": 3325.00,
          "total": 3956.25,
          "distribution_center_code": "DC-BOG-001",
          "stock_confirmed": true,
          "stock_confirmation_date": "2025-10-16T14:30:05",
          "created_at": "2025-10-16T14:30:00"
        },
        {
          "id": 2,
          "order_id": 1,
          "product_sku": "VAC-001",
          "product_name": "Vacuna Hepatitis B",
          "quantity": 5,
          "unit_price": 1500.00,
          "discount_percentage": 0.00,
          "discount_amount": 0.00,
          "tax_percentage": 19.00,
          "tax_amount": 1425.00,
          "subtotal": 7500.00,
          "total": 8925.00,
          "distribution_center_code": "DC-BOG-001",
          "stock_confirmed": true,
          "stock_confirmation_date": "2025-10-16T14:30:05",
          "created_at": "2025-10-16T14:30:00"
        }
      ]
    },
    {
      "id": 2,
      "order_number": "ORD-20251015-0005",
      "customer_id": 3,
      "seller_id": "SELLER-001",
      "seller_name": "Juan Pérez",
      "order_date": "2025-10-15T10:15:00",
      "status": "confirmed",
      "subtotal": 25000.00,
      "discount_amount": 0.00,
      "tax_amount": 4750.00,
      "total_amount": 29750.00,
      "payment_terms": "contado",
      "payment_method": "efectivo",
      "delivery_address": "Avenida 45 #12-34",
      "delivery_city": "Medellín",
      "delivery_department": "Antioquia",
      "preferred_distribution_center": "DC-MED-001",
      "notes": null,
      "created_at": "2025-10-15T10:15:00",
      "updated_at": "2025-10-15T11:20:00",
      "items": [
        {
          "id": 3,
          "order_id": 2,
          "product_sku": "GUA-001",
          "product_name": "Guantes de látex talla M (caja 100 unidades)",
          "quantity": 20,
          "unit_price": 1250.00,
          "discount_percentage": 0.00,
          "discount_amount": 0.00,
          "tax_percentage": 19.00,
          "tax_amount": 4750.00,
          "subtotal": 25000.00,
          "total": 29750.00,
          "distribution_center_code": "DC-MED-001",
          "stock_confirmed": true,
          "stock_confirmation_date": "2025-10-15T10:15:03",
          "created_at": "2025-10-15T10:15:00"
        }
      ]
    }
  ],
  "total": 2
}
```

### Respuesta Sin Resultados

Cuando no hay órdenes que coincidan con los filtros:

```json
{
  "orders": [],
  "total": 0
}
```

### Códigos de Estado HTTP

| Código | Descripción |
|--------|-------------|
| `200 OK` | La solicitud fue procesada exitosamente |
| `500 Internal Server Error` | Error interno del servidor (error en base de datos, etc.) |

---

## Funcionamiento Interno

### Flujo de Ejecución

1. **Recepción de Request**: El blueprint `orders_bp` recibe la solicitud GET en el endpoint `/orders`

2. **Extracción de Parámetros**: Se extraen los query parameters opcionales:
   - `customer_id` (integer)
   - `seller_id` (string)
   - `status` (string)

3. **Instanciación del Command**: Se crea una instancia de `GetOrders` con los filtros proporcionados:
   ```python
   command = GetOrders(
       customer_id=customer_id,
       seller_id=seller_id,
       status=status
   )
   ```

4. **Ejecución del Command**: Se ejecuta el método `execute()` que:
   - Construye una consulta base desde el modelo `Order`
   - Aplica filtros dinámicamente según los parámetros recibidos:
     - Si hay `customer_id`: filtra por cliente
     - Si hay `seller_id`: **filtra por vendedor** (caso de uso principal)
     - Si hay `status`: filtra por estado
   - Ordena los resultados por fecha descendente (más recientes primero)
   - Ejecuta la consulta en la base de datos

5. **Serialización**: Cada orden se convierte a diccionario mediante `to_dict(include_items=True)`, incluyendo:
   - Todos los campos de la orden
   - Los ítems relacionados con sus detalles completos

6. **Construcción de Response**: Se construye el objeto JSON de respuesta con:
   - Array de órdenes serializadas
   - Total de registros encontrados

7. **Envío de Response**: Se retorna el JSON con código HTTP 200

### Diagrama de Flujo

```
┌─────────────────┐
│   Cliente App   │
│    Vendedor     │
└────────┬────────┘
         │ GET /orders?seller_id=SELLER-001
         ▼
┌─────────────────────────────────────┐
│  Blueprint: orders_bp               │
│  Endpoint: get_orders()             │
│  - Extrae query params              │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Command: GetOrders                 │
│  - Recibe filtros                   │
│  - Construye query                  │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Model: Order                       │
│  - Aplica filtros SQL:              │
│    • customer_id (opcional)         │
│    • seller_id (principal)          │
│    • status (opcional)              │
│  - ORDER BY order_date DESC         │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Database Query                     │
│  SELECT * FROM orders               │
│  WHERE seller_id = 'SELLER-001'     │
│  ORDER BY order_date DESC           │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Serialización                      │
│  - order.to_dict(include_items=True)│
│  - Incluye items relacionados       │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Response JSON                      │
│  {                                  │
│    "orders": [...],                 │
│    "total": n                       │
│  }                                  │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────┐
│   Cliente App   │
│  (200 OK)       │
└─────────────────┘
```

---

## Casos de Uso

### Caso de Uso Principal: Vendedor Consultando sus Órdenes

**Actor**: Vendedor móvil usando la aplicación

**Objetivo**: Obtener el listado completo de todas sus órdenes registradas

**Flujo**:
1. El vendedor abre la aplicación móvil
2. La app identifica el `seller_id` del vendedor autenticado (ej: "SELLER-001")
3. La app realiza una petición GET a `/orders?seller_id=SELLER-001`
4. El sistema retorna todas las órdenes del vendedor ordenadas por fecha
5. La app muestra el listado de órdenes con sus detalles

### Caso de Uso 2: Vendedor Filtrando Órdenes Pendientes

**Actor**: Vendedor

**Objetivo**: Ver solo las órdenes que están pendientes de confirmación

**Flujo**:
1. El vendedor selecciona el filtro "Pendientes" en la app
2. La app realiza GET a `/orders?seller_id=SELLER-001&status=pending`
3. El sistema retorna solo las órdenes en estado "pending"
4. El vendedor puede priorizar el seguimiento de estas órdenes

### Caso de Uso 3: Vendedor Revisando Órdenes de un Cliente

**Actor**: Vendedor

**Objetivo**: Ver el historial de órdenes de un cliente específico

**Flujo**:
1. El vendedor busca un cliente (ej: ID 5)
2. Selecciona ver historial de órdenes
3. La app realiza GET a `/orders?seller_id=SELLER-001&customer_id=5`
4. El sistema retorna solo las órdenes del vendedor para ese cliente
5. El vendedor puede revisar patrones de compra y hacer seguimiento

---

## Consideraciones Técnicas

### Base de Datos

- **Motor**: PostgreSQL (inferido de la configuración)
- **Tabla Principal**: `orders`
- **Índices**: La columna `order_number` tiene índice único, y `product_sku` en items tiene índice
- **Relaciones**:
  - `Order` ← `OrderItem` (one-to-many)
  - `Order` → `Customer` (many-to-one)

### Performance

- **Ordenamiento**: Las órdenes se ordenan por `order_date DESC` para mostrar las más recientes primero
- **Eager Loading**: Los items se cargan con cada orden usando `include_items=True`
- **Paginación**: No implementada actualmente - puede ser necesaria con grandes volúmenes

### Validaciones

- Los query parameters son opcionales, permitiendo consultas flexibles
- El tipo de dato de `customer_id` se convierte explícitamente a `integer`
- Si no hay filtros, se retornan todas las órdenes del sistema

### Extensibilidad

El diseño permite fácilmente agregar:
- Nuevos filtros (ej: rango de fechas, ciudad de entrega)
- Paginación (limit/offset)
- Ordenamiento personalizado
- Campos adicionales de búsqueda

---

## Ejemplos de Integración

### JavaScript/React Native (Aplicación Móvil)

```javascript
async function getSellerOrders(sellerId, filters = {}) {
  try {
    // Construir query params
    const params = new URLSearchParams({
      seller_id: sellerId,
      ...filters
    });
    
    const response = await fetch(
      `http://localhost:3003/orders?${params}`,
      {
        method: 'GET',
        headers: {
          'Accept': 'application/json'
        }
      }
    );
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    return data; // { orders: [...], total: n }
  } catch (error) {
    console.error('Error fetching seller orders:', error);
    throw error;
  }
}

// Uso
const sellerOrders = await getSellerOrders('SELLER-001');
console.log(`Total órdenes: ${sellerOrders.total}`);

// Con filtros
const pendingOrders = await getSellerOrders('SELLER-001', { 
  status: 'pending' 
});
```

### Python (Cliente)

```python
import requests

def get_seller_orders(seller_id, customer_id=None, status=None):
    """Obtiene las órdenes de un vendedor."""
    url = 'http://localhost:3003/orders'
    
    params = {'seller_id': seller_id}
    if customer_id:
        params['customer_id'] = customer_id
    if status:
        params['status'] = status
    
    response = requests.get(url, params=params)
    response.raise_for_status()
    
    return response.json()

# Uso
orders_data = get_seller_orders('SELLER-001')
print(f"Total órdenes: {orders_data['total']}")

for order in orders_data['orders']:
    print(f"Orden {order['order_number']}: {order['status']}")
    print(f"  Total: ${order['total_amount']}")
    print(f"  Items: {len(order['items'])}")
```

### cURL (Testing)

```bash
# Obtener todas las órdenes de un vendedor
curl -X GET "http://localhost:3003/orders?seller_id=SELLER-001" \
     -H "Accept: application/json"

# Con múltiples filtros
curl -X GET "http://localhost:3003/orders?seller_id=SELLER-001&status=pending&customer_id=5" \
     -H "Accept: application/json"

# Formatear respuesta con jq
curl -s "http://localhost:3003/orders?seller_id=SELLER-001" | jq '.orders[] | {order_number, status, total_amount}'
```

---

## Testing

El endpoint cuenta con pruebas automatizadas que verifican:

✅ Obtención de todas las órdenes sin filtros  
✅ Filtrado por `customer_id`  
✅ **Filtrado por `seller_id`** (caso principal)  
✅ Filtrado por `status`  
✅ Combinación de múltiples filtros  
✅ Ordenamiento por fecha descendente  
✅ Caso sin resultados  

### Ejecutar Tests

```bash
# Todos los tests del blueprint
pipenv run pytest tests/blueprints/test_blueprints_orders.py -v

# Test específico de filtrado por vendedor
pipenv run pytest tests/blueprints/test_blueprints_orders.py::TestOrdersBlueprint::test_get_orders_by_seller -v

# Con cobertura
pipenv run pytest tests/ --cov=src.commands.get_orders --cov-report=term-missing
```

---

## Mejoras Sugeridas

### 1. Paginación
Implementar `limit` y `offset` para manejar grandes volúmenes:
```python
page = request.args.get('page', 1, type=int)
per_page = request.args.get('per_page', 20, type=int)
```

### 2. Filtro por Rango de Fechas
```python
start_date = request.args.get('start_date')
end_date = request.args.get('end_date')
```

### 3. Búsqueda por Número de Orden
```python
order_number = request.args.get('order_number')
```

### 4. Ordenamiento Personalizado
```python
sort_by = request.args.get('sort_by', 'order_date')
sort_order = request.args.get('sort_order', 'desc')
```

### 5. Caching
Implementar cache para consultas frecuentes de vendedores específicos.

### 6. Autenticación/Autorización
Validar que el vendedor solo pueda ver sus propias órdenes:
```python
if authenticated_seller_id != seller_id:
    return jsonify({'error': 'Unauthorized'}), 403
```

---

## Conclusión

El endpoint `GET /orders` con filtro por `seller_id` es una funcionalidad esencial para que los vendedores móviles puedan consultar y gestionar sus órdenes en tiempo real. La implementación actual es:

- ✅ **Simple y efectiva**: Filtrado flexible mediante query parameters
- ✅ **Completa**: Incluye toda la información de órdenes e ítems
- ✅ **Ordenada**: Resultados ordenados por fecha descendente
- ✅ **Bien testeada**: Cobertura de tests automatizados
- ✅ **Extensible**: Fácil agregar nuevos filtros y funcionalidades

Esta documentación proporciona toda la información necesaria para integrar este endpoint en aplicaciones cliente, especialmente aplicaciones móviles para vendedores.

---

**Fecha de Documentación**: 16 de octubre de 2025  
**Versión del Servicio**: 1.0.0  
**Microservicio**: sales-service  
**Puerto**: 3003
