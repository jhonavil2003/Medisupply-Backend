# MediSupply - Logistics Service

Microservicio de logística e inventario para la plataforma MediSupply.


## Quick Start

### Con Docker Compose

```bash
# Construir e iniciar servicios
docker-compose up -d --build

# Verificar que los servicios están corriendo
docker-compose ps

# Seed inicial de datos
docker-compose exec logistics-service python seed_data.py

# Ver logs
docker-compose logs -f logistics-service
```


##  Endpoints

### `GET /inventory/stock-levels`

Consulta niveles de stock en tiempo real por producto y centro de distribución.

**Query Parameters:**

| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `product_sku` | string | Sí* | SKU del producto (consulta individual) |
| `product_skus` | string | Sí* | SKUs separados por coma (consulta múltiple) |
| `distribution_center_id` | integer | No | Filtrar por centro específico |
| `only_available` | boolean | No | Solo productos con stock disponible (default: false) |
| `include_reserved` | boolean | No | Incluir cantidades reservadas (default: true) |
| `include_in_transit` | boolean | No | Incluir cantidades en tránsito (default: false) |

*Nota: Se requiere `product_sku` O `product_skus`, no ambos.


**Ejemplos de uso:**

```bash
# Consultar stock de un producto
curl "http://localhost:3002/inventory/stock-levels?product_sku=JER-001"

# Consultar múltiples productos
curl "http://localhost:3002/inventory/stock-levels?product_skus=JER-001,VAC-001,GUANTE-001"

# Filtrar por centro de distribución
curl "http://localhost:3002/inventory/stock-levels?product_sku=JER-001&distribution_center_id=1"

# Solo productos con stock disponible
curl "http://localhost:3002/inventory/stock-levels?product_skus=JER-001,GUANTE-001&only_available=true"

# Incluir cantidades en tránsito
curl "http://localhost:3002/inventory/stock-levels?product_sku=JER-001&include_in_transit=true"
```

### `GET /inventory/health`

Health check del microservicio.

**Respuesta:**

```json
{
  "status": "healthy",
  "service": "logistics-service",
  "version": "1.0.0"
}
```


## 🧪 Testing

### Ejecutar Tests

```bash
# Todos los tests con cobertura
pipenv run pytest tests/ -v --cov=src --cov-report=term-missing
```

