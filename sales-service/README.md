# Sales Service - MediSupply Backend

Microservicio de ventas (sales-service) que implementa la funcionalidad de gestión de pedidos con validación de stock en tiempo real para el sistema MediSupply.

## 🎯 Propósito

Este microservicio implementa la **Historia de Usuario HU-102**: "Como vendedor, quiero crear un pedido desde mi app móvil durante la visita a un cliente, consultando la disponibilidad en tiempo real de cada producto que agrego, para cerrar la venta con la certeza de poder cumplir con la entrega."

### Funcionalidades Principales

- ✅ Gestión de clientes (hospitales, clínicas, farmacias, distribuidores)
- ✅ Creación de pedidos con validación de stock en tiempo real
- ✅ Integración con `catalog-service` para validar productos
- ✅ Integración con `logistics-service` para validar disponibilidad
- ✅ Cálculo automático de totales, descuentos e impuestos
- ✅ Asignación inteligente de centros de distribución

## 📦 Arquitectura

```
sales-service/
├── src/
│   ├── models/              # Modelos de datos (Customer, Order, OrderItem, CommercialCondition)
│   ├── commands/            # Lógica de negocio (CreateOrder, GetCustomers, GetOrders)
│   ├── blueprints/          # Rutas REST API (customers, orders)
│   ├── services/            # Servicios de integración (IntegrationService)
│   ├── errors/              # Manejo de errores
│   ├── session.py           # Configuración de base de datos
│   └── main.py              # Aplicación Flask
├── tests/                   # Suite de tests
├── docker-compose.yml       # Orquestación de contenedores
├── Dockerfile               # Imagen del servicio
├── Pipfile                  # Dependencias Python
└── seed_data.py             # Datos de ejemplo
```

## 🚀 Quick Start

### Prerrequisitos

- Python 3.9+
- Docker & Docker Compose
- `catalog-service` corriendo en puerto 3001
- `logistics-service` corriendo en puerto 3002

### 1. Configurar variables de entorno

```bash
cp .env.example .env
nano .env
```

**⚠️ IMPORTANTE**: Cambia `POSTGRES_PASSWORD=change_me_in_production` por una contraseña segura.

### 2. Levantar servicios

```bash
# Construir y levantar contenedores
docker-compose up -d --build

# Verificar que estén corriendo
docker-compose ps
```

### 3. Cargar datos de ejemplo

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

## 🔗 Integración con Otros Microservicios

### Flujo HU-102: Crear Pedido con Validación en Tiempo Real

```
┌─────────────┐       ┌──────────────┐       ┌───────────────┐       ┌──────────────────┐
│  App Móvil  │──────>│ Sales Service│──────>│Catalog Service│       │Logistics Service │
│  (Vendedor) │       │  (Puerto 3003│       │  (Puerto 3001)│       │   (Puerto 3002)  │
└─────────────┘       └──────────────┘       └───────────────┘       └──────────────────┘
       │                      │                       │                         │
       │  POST /orders        │                       │                         │
       │─────────────────────>│                       │                         │
       │                      │                       │                         │
       │                      │  GET /products/{sku}  │                         │
       │                      │──────────────────────>│                         │
       │                      │                       │                         │
       │                      │  ✅ Product Info      │                         │
       │                      │<──────────────────────│                         │
       │                      │                                                 │
       │                      │  GET /inventory/stock-levels?product_sku={sku} │
       │                      │────────────────────────────────────────────────>│
       │                      │                                                 │
       │                      │  ✅ Stock Available (325 unidades)              │
       │                      │<────────────────────────────────────────────────│
       │                      │                                                 │
       │  ✅ Order Created    │                                                 │
       │<─────────────────────│                                                 │
       │  (201)               │                                                 │
```

### Validaciones Implementadas

1. **Validación de Producto** (catalog-service):
   - Producto existe
   - Producto está activo
   - Precio unitario válido

2. **Validación de Stock** (logistics-service):
   - Stock disponible >= cantidad solicitada
   - Selección del centro de distribución óptimo
   - Flags `is_low_stock` y `is_out_of_stock`

3. **Validaciones de Negocio**:
   - Cliente existe y está activo
   - Cantidades válidas (> 0)
   - Cálculo correcto de descuentos e impuestos

## 🗄️ Modelos de Datos

### Customer (Cliente)
```python
{
  "id": int,
  "document_type": str,        # NIT, CC, CE
  "document_number": str,
  "business_name": str,
  "customer_type": str,        # hospital, clinica, farmacia, distribuidor
  "city": str,
  "credit_limit": decimal,
  "credit_days": int,
  "is_active": bool
}
```

### Order (Pedido)
```python
{
  "id": int,
  "order_number": str,         # ORD-YYYYMMDD-XXXX
  "customer_id": int,
  "seller_id": str,
  "status": str,               # pending, confirmed, processing, shipped, delivered, cancelled
  "subtotal": decimal,
  "discount_amount": decimal,
  "tax_amount": decimal,
  "total_amount": decimal,
  "payment_terms": str,        # contado, credito_30, credito_60, credito_90
  "items": [OrderItem]
}
```

### OrderItem (Línea de Pedido)
```python
{
  "id": int,
  "product_sku": str,
  "product_name": str,
  "quantity": int,
  "unit_price": decimal,
  "discount_percentage": decimal,
  "tax_percentage": decimal,
  "stock_confirmed": bool,
  "distribution_center_code": str
}
```

## 🧪 Testing

```bash
# Instalar dependencias
pipenv install --dev

# Ejecutar todos los tests
pipenv run pytest tests/ -v

# Con cobertura
pipenv run pytest tests/ --cov=src --cov-report=term-missing

# Tests específicos
pipenv run pytest tests/models/ -v
pipenv run pytest tests/commands/ -v
pipenv run pytest tests/blueprints/ -v
```

## 🔐 Seguridad

### Credenciales

- ✅ Sin credenciales hardcodeadas en el código
- ✅ Todas las credenciales en variables de entorno
- ✅ `.env` excluido en `.gitignore`
- ✅ `.env.example` con valores placeholder seguros

### Buenas Prácticas

1. Cambiar `POSTGRES_PASSWORD` en producción
2. Usar HTTPS en producción
3. Implementar autenticación y autorización (JWT/OAuth)
4. Validar y sanitizar todas las entradas
5. Implementar rate limiting
6. Logs de auditoría para operaciones críticas

## 🐳 Docker

### Puertos

- **3003**: Sales Service API
- **5434**: PostgreSQL Database

### Comandos útiles

```bash
# Ver logs
docker-compose logs -f sales-service

# Reiniciar servicio
docker-compose restart sales-service

# Detener todo
docker-compose down

# Detener y eliminar volúmenes
docker-compose down -v

# Ejecutar comando en contenedor
docker-compose exec sales-service python seed_data.py
```

## 📊 Cumplimiento HU-102

| Criterio de Aceptación | Estado |
|------------------------|--------|
| Iniciar nuevo pedido desde app móvil | ✅ POST /orders |
| Buscar productos por nombre, código o categoría | ✅ Integración con catalog-service |
| Consultar disponibilidad en tiempo real | ✅ Integración con logistics-service |
| Discriminada por centro de distribución | ✅ Campo `distribution_center_code` |
| Advertencia si no hay inventario | ✅ Error 409 con detalles de stock |
| Datos del cliente | ✅ Campo `customer_id` y relación |
| Lista de productos con disponibilidad confirmada | ✅ Campo `stock_confirmed` en OrderItem |
| Condiciones comerciales (descuentos, impuestos) | ✅ Modelo CommercialCondition |
| Validación antes de confirmar | ✅ Validación en CreateOrder command |
| Registro en sistema central | ✅ Base de datos PostgreSQL |
| Visible para logística y bodega | ✅ API GET /orders |
| Tiempo de respuesta < 3 segundos | ✅ Timeout configurado en 3s |

## 🚀 Deploy a Producción

### Checklist

- [ ] Cambiar `POSTGRES_PASSWORD` a valor seguro
- [ ] Configurar URLs de servicios externos (catalog, logistics)
- [ ] Habilitar SSL/TLS
- [ ] Implementar autenticación (JWT)
- [ ] Configurar rate limiting
- [ ] Implementar monitoreo y alertas
- [ ] Configurar backups automáticos
- [ ] Implementar circuit breakers para servicios externos
- [ ] Logs centralizados (ELK, CloudWatch)
- [ ] Health checks configurados

## 📞 Soporte

Para reportar issues o solicitar features, crear un ticket en el repositorio del proyecto.

---

**Versión**: 1.0.0  
**Fecha**: Octubre 2025  
**Autor**: MediSupply Team
