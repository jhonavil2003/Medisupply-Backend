# MediSupply - Catalog Service

Microservicio de catálogo de productos para la plataforma MediSupply.

## Quick Start

### Con Docker Compose

```bash
# Construir e iniciar servicios
docker-compose up -d --build

# Verificar que los servicios están corriendo
docker-compose ps

# Seed inicial de datos
docker-compose exec catalog-service python seed_data.py

```

##  Endpoints

### `GET /products`
Lista productos con filtros opcionales.

**Query Parameters:**
- `search`: Búsqueda en nombre/descripción
- `sku`: Filtrar por SKU específico
- `category`: Filtrar por categoría
- `cold_chain`: true/false para cadena de frío
- `page`: Número de página (default: 1)
- `per_page`: Items por página (default: 10)

**Ejemplo:**
```bash
curl "http://localhost:3001/products?search=jeringa&category=Instrumental"
```

### `GET /products/{sku}`
Obtiene detalle completo de un producto por SKU.

**Ejemplo:**
```bash
curl "http://localhost:3001/products/JER-001"
```

## Configuración

Variables de entorno en `.env`:

```properties
FLASK_ENV=development
DATABASE_URL=postgresql://postgres:postgres@db:5432/catalog_db
PORT=3001
HOST=0.0.0.0
```


## Testing

### Ejecutar Tests

```bash
pipenv run pytest --cov=src --cov-report=term-missing
```

### Ejemplos de Uso

```bash
# Health check
curl http://localhost:3001/health

# Listar productos
curl http://localhost:3001/products

# Buscar por SKU
curl http://localhost:3001/products/JER-001
```