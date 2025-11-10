# Sales Service - MediSupply Backend

Servicio de ventas con capacidades de tracking de órdenes, filtrado avanzado por fechas, estado y cliente.

**Características principales:**
- ✅ Gestión completa de clientes y órdenes
- ✅ Filtros avanzados por fechas, estado y cliente  
- ✅ Tracking de órdenes en tiempo real
- ✅ Integración con servicios de catálogo y logística
- ✅ Validación de stock en tiempo real
- ✅ **Gestión de objetivos de vendedores (Salesperson Goals)** - NUEVO ✨
  - CRUD completo con validaciones de negocio
  - Objetivos por región, trimestre y tipo (monetario/unidades)
  - Integración con productos del catálogo
  - 100% de cobertura en tests unitarios

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

# Obtener pedidos con filtros
curl "http://localhost:3003/orders?customer_id=1&status=pending"

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
  "customer_id": 1,                    // ID del cliente (requerido)
  "seller_id": "SELLER-001",          // ID del vendedor (requerido) 
  "seller_name": "Juan Perez",        // Nombre del vendedor (opcional)
  "items": [                          // Lista de productos (requerido)
    {
      "product_sku": "JER-001",       // SKU del producto (requerido)
      "quantity": 10,                 // Cantidad (requerido)
      "discount_percentage": 5.0,     // Descuento % (opcional, default: 0.0)
      "tax_percentage": 19.0          // Impuesto % (opcional, default: 19.0)
    }
  ],
  // Campos opcionales con valores permitidos:
  "payment_terms": "credito_30",      // contado, credito_30, credito_60, credito_90
  "payment_method": "transferencia",  // transferencia, cheque, efectivo
  "delivery_address": "Calle 10 #5-25",
  "delivery_city": "Bogota",
  "delivery_department": "Cundinamarca", 
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
- `status` (opcional): Estado del pedido (pending, confirmed, processing, shipped, delivered, cancelled)
- `delivery_date_from` (opcional): Fecha desde (formato: YYYY-MM-DD) - usa order_date como proxy
- `delivery_date_to` (opcional): Fecha hasta (formato: YYYY-MM-DD) - usa order_date como proxy
- `order_date_from` (opcional): Fecha de orden desde (formato: YYYY-MM-DD)
- `order_date_to` (opcional): Fecha de orden hasta (formato: YYYY-MM-DD)

**Ejemplos:**
```bash
# Básico: pedidos de cliente específico
curl "http://localhost:3003/orders?customer_id=1"

# Con filtro de estado
curl "http://localhost:3003/orders?customer_id=1&status=pending"

# Con filtro de fechas
curl "http://localhost:3003/orders?customer_id=1&delivery_date_from=2025-10-01&delivery_date_to=2025-10-31"

# Filtro completo: cliente + estado + fechas
curl "http://localhost:3003/orders?customer_id=1&status=confirmed&delivery_date_from=2025-10-01&delivery_date_to=2025-12-31"

# PowerShell equivalente
Invoke-RestMethod -Uri "http://localhost:3003/orders?customer_id=1&status=pending&delivery_date_from=2025-10-01&delivery_date_to=2025-10-31" -Method GET
```

#### GET /orders/{id}
Obtener detalle completo de un pedido.

**Ejemplo:**
```bash
curl http://localhost:3003/orders/1
```

#### DELETE /orders/{id}
Eliminar una orden por ID.

**Path Parameters:**
- `id` (requerido): ID de la orden a eliminar

**Respuesta Exitosa (200):**
```json
{
  "message": "Order ORD-20251017-0001 deleted successfully",
  "deleted_order": {
    "id": 1,
    "order_number": "ORD-20251017-0001",
    "customer_id": 1,
    "seller_id": "SELLER-002",
    "status": "pending",
    "total_amount": 5.62
  }
}
```

**Errores posibles:**
- `404` - Orden no encontrada

**Ejemplo:**
```bash
# Eliminar orden con ID 1
curl -X DELETE http://localhost:3003/orders/1

# Con respuesta formateada
curl -X DELETE http://localhost:3003/orders/1 | python3 -m json.tool
```

**Nota:** La eliminación es en cascada, por lo que también se eliminarán todos los ítems relacionados con la orden.

## 🔍 **Filtros Avanzados para Órdenes**

### **Casos de Uso Comunes**

#### 1. **Pedidos por cliente y estado**
```bash
# Pedidos pendientes del cliente 1
curl "http://localhost:3003/orders?customer_id=1&status=pending"

# Pedidos confirmados del cliente 2
curl "http://localhost:3003/orders?customer_id=2&status=confirmed"
```

#### 2. **Filtros por fechas (tracking de órdenes)**
```bash
# Pedidos del mes de octubre 2025
curl "http://localhost:3003/orders?delivery_date_from=2025-10-01&delivery_date_to=2025-10-31"

# Pedidos de los últimos 7 días
curl "http://localhost:3003/orders?order_date_from=2025-10-13&order_date_to=2025-10-20"

# Pedidos de un cliente en rango específico
curl "http://localhost:3003/orders?customer_id=1&delivery_date_from=2025-10-01&delivery_date_to=2025-12-31"
```

#### 3. **Filtros por vendedor**
```bash
# Todos los pedidos de un vendedor
curl "http://localhost:3003/orders?seller_id=SELLER-001"

# Pedidos de un vendedor en estado específico
curl "http://localhost:3003/orders?seller_id=SELLER-001&status=shipped"
```

#### 4. **Filtros combinados (reporte completo)**
```bash
# Reporte: cliente específico, estado confirmado, últimos 30 días
curl "http://localhost:3003/orders?customer_id=1&status=confirmed&delivery_date_from=2025-10-01&delivery_date_to=2025-10-30"
```

### **Estados y Valores del Sistema**

#### **🔄 Estados de Pedidos (`status`)**
- `pending` - Pedido creado, esperando confirmación (default)
- `confirmed` - Pedido confirmado, en proceso
- `processing` - Pedido en preparación
- `shipped` - Pedido enviado
- `delivered` - Pedido entregado
- `cancelled` - Pedido cancelado

#### **💳 Términos de Pago (`payment_terms`)**
- `contado` - Pago de contado/inmediato (default)
- `credito_30` - Crédito a 30 días
- `credito_60` - Crédito a 60 días
- `credito_90` - Crédito a 90 días

#### **💰 Métodos de Pago (`payment_method`)**
- `transferencia` - Transferencia bancaria
- `cheque` - Pago con cheque
- `efectivo` - Pago en efectivo

#### **🏥 Tipos de Cliente (`customer_type`)**
- `hospital` - Hospital
- `clinica` - Clínica
- `farmacia` - Farmacia
- `eps` - Entidad Promotora de Salud
- `ips` - Institución Prestadora de Servicios

#### **✅ Estados de Stock (`stock_confirmed`)**
- `true` - Stock confirmado/disponible
- `false` - Stock no confirmado/insuficiente (default)

### **📊 Ejemplos de Filtrado por Estados**

```bash
# Filtrar por diferentes estados de pedidos
curl "http://localhost:3003/orders?status=pending"
curl "http://localhost:3003/orders?status=confirmed"
curl "http://localhost:3003/orders?status=delivered"

# Combinar cliente con estado específico
curl "http://localhost:3003/orders?customer_id=1&status=processing"

# Filtrar pedidos por términos de pago
curl "http://localhost:3003/orders?customer_id=1" # Todos los términos
# Nota: Actualmente no hay filtro directo por payment_terms, usar respuesta completa

# Ejemplo de creación con estados específicos
curl -X POST "http://localhost:3003/orders" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": 1,
    "seller_id": "SELLER-001",
    "items": [{"product_sku": "JER-001", "quantity": 5}],
    "payment_terms": "credito_30",
    "payment_method": "transferencia"
  }'
```

### **PowerShell - Ejemplos Prácticos**
```powershell
# Obtener pedidos y mostrar solo el total
$response = Invoke-RestMethod -Uri "http://localhost:3003/orders?customer_id=1" -Method GET
Write-Host "Total pedidos cliente 1: $($response.total)"

# Filtro con fechas y formatear salida
$response = Invoke-RestMethod -Uri "http://localhost:3003/orders?customer_id=1&delivery_date_from=2025-10-01&delivery_date_to=2025-10-31" -Method GET
$response | ConvertTo-Json -Depth 3

# Obtener solo los números de orden
$response = Invoke-RestMethod -Uri "http://localhost:3003/orders?customer_id=1" -Method GET
$response.orders | ForEach-Object { Write-Host "Orden: $($_.order_number) - Estado: $($_.status)" }
```

---

## 📚 **Referencia Rápida - Valores Permitidos**

| Campo | Valores Permitidos | Default |
|-------|-------------------|---------|
| **status** | `pending`, `confirmed`, `processing`, `shipped`, `delivered`, `cancelled` | `pending` |
| **payment_terms** | `contado`, `credito_30`, `credito_60`, `credito_90` | `contado` |
| **payment_method** | `transferencia`, `cheque`, `efectivo` | - |
| **customer_type** | `hospital`, `clinica`, `farmacia`, `eps`, `ips` | - |
| **stock_confirmed** | `true`, `false` | `false` |

### **Endpoints Principales**
```bash
# Salud del servicio
GET /health

# Clientes
GET /customers                    # Listar todos
GET /customers/{id}              # Obtener por ID
POST /customers                  # Crear nuevo

# Órdenes  
GET /orders                      # Listar con filtros
GET /orders/{id}                 # Obtener por ID
POST /orders                     # Crear nueva
DELETE /orders/{id}              # Eliminar
```

##  Testing

```bash

# Con cobertura
pipenv run pytest tests/ --cov=src --cov-report=term-missing

```