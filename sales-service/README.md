# Sales Service - MediSupply Backend

##  Quick Start

###  Levantar servicios

```bash
# Construir y levantar contenedores
docker-compose up -d --build

# Verificar que estén corriendo
docker-compose ps
```

### Cargar datos de ejemplo

```bash
docker-compose exec sales-service python seed_data.py
```

### 4. Probar el servicio

```bash
# Health check
curl http://localhost:3003/health

# Obtener clientes
curl http://localhost:3003/customers

# Crear un pedido (requiere catalog-service y logistics-service corriendo)
curl -X POST http://localhost:3003/orders \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": 1,
    "seller_id": "SELLER-001",
    "seller_name": "Juan Pérez",
    "items": [
      {
        "product_sku": "JER-001",
        "quantity": 10
      }
    ],
    "payment_terms": "credito_30"
  }'
```

## 📚 API Endpoints

### Customers (Clientes)

#### GET /customers
Obtener lista de clientes con filtros opcionales.

**Query Parameters:**
- `customer_type` (opcional): Tipo de cliente (hospital, clinica, farmacia, distribuidor)
- `city` (opcional): Ciudad
- `is_active` (opcional): Estado activo (true/false)

**Ejemplo:**
```bash
curl "http://localhost:3003/customers?customer_type=hospital&city=Bogotá"
```

**Respuesta:**
```json
{
  "customers": [
    {
      "id": 1,
      "document_type": "NIT",
      "document_number": "900123456-1",
      "business_name": "Hospital Universitario San Ignacio",
      "customer_type": "hospital",
      "city": "Bogotá",
      "credit_limit": 50000000.0,
      "credit_days": 60,
      "is_active": true
    }
  ],
  "total": 1
}
```

#### GET /customers/{id}
Obtener detalle de un cliente específico.

**Ejemplo:**
```bash
curl http://localhost:3003/customers/1
```

### Orders (Pedidos)

#### POST /orders
Crear un nuevo pedido con validación de stock en tiempo real **(HU-102)**.

**Request Body:**
```json
{
  "customer_id": 1,
  "seller_id": "SELLER-001",
  "seller_name": "Juan Pérez",
  "items": [
    {
      "product_sku": "JER-001",
      "quantity": 10,
      "discount_percentage": 5.0
    },
    {
      "product_sku": "VAC-001",
      "quantity": 5
    }
  ],
  "payment_terms": "credito_30",
  "payment_method": "transferencia",
  "preferred_distribution_center": "DC-BOG-001",
  "notes": "Entrega urgente"
}
```

**Respuesta Exitosa (201):**
```json
{
  "id": 1,
  "order_number": "ORD-20251011-0001",
  "customer_id": 1,
  "seller_id": "SELLER-001",
  "status": "pending",
  "subtotal": 10500.0,
  "discount_amount": 525.0,
  "tax_amount": 1895.25,
  "total_amount": 11870.25,
  "items": [
    {
      "product_sku": "JER-001",
      "product_name": "Jeringa desechable 3ml",
      "quantity": 10,
      "unit_price": 350.0,
      "stock_confirmed": true,
      "distribution_center_code": "DC-BOG-001"
    }
  ],
  "customer": {
    "business_name": "Hospital Universitario San Ignacio",
    "city": "Bogotá"
  }
}
```

**Errores posibles:**
- `400` - Validación fallida (campos requeridos, cantidad inválida)
- `404` - Cliente o producto no encontrado
- `409` - Stock insuficiente
- `503` - Servicios externos no disponibles

#### GET /orders
Obtener lista de pedidos con filtros opcionales.

**Query Parameters:**
- `customer_id` (opcional): ID del cliente
- `seller_id` (opcional): ID del vendedor
- `status` (opcional): Estado del pedido

**Ejemplo:**
```bash
curl "http://localhost:3003/orders?customer_id=1&status=pending"
```

#### GET /orders/{id}
Obtener detalle completo de un pedido.

**Ejemplo:**
```bash
curl http://localhost:3003/orders/1
```



##  Testing

```bash

# Con cobertura
pipenv run pytest tests/ --cov=src --cov-report=term-missing

```