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
- `search`: Búsqueda en nombre/descripción/SKU/barcode/manufacturer
- `sku`: Filtrar por SKU específico (coincidencia parcial)
- `category`: Filtrar por categoría
- `subcategory`: Filtrar por subcategoría
- `supplier_id`: Filtrar por ID del proveedor
- `is_active`: true/false para productos activos (default: true)
- `requires_cold_chain`: true/false para cadena de frío
- `page`: Número de página (default: 1)
- `per_page`: Items por página (default: 20, max: 100)

**Ejemplos:**
```bash
# Buscar por término general
curl "http://localhost:3001/products?search=jeringa&category=Instrumental"

# Buscar producto específico por SKU
curl "http://localhost:3001/products?sku=MED-2025-001"

# Filtrar por proveedor específico
curl "http://localhost:3001/products?supplier_id=1"

# Paginación
curl "http://localhost:3001/products?page=2&per_page=10"
```

### `POST /products`
Crear un nuevo producto.

**Request Body:**
```json
{
  "sku": "JER-002",
  "name": "Jeringa desechable 5ml",
  "description": "Jeringa estéril de 5ml con aguja 22G",
  "category": "Instrumental",
  "subcategory": "Descartables",
  "unit_price": 450.00,
  "currency": "USD",
  "unit_of_measure": "unidad",
  "supplier_id": 1,
  "requires_cold_chain": false,
  "manufacturer": "BD Medical",
  "country_of_origin": "Colombia"
}
```

**Ejemplo:**
```bash
curl -X POST "http://localhost:3001/products" \
  -H "Content-Type: application/json" \
  -d '{"sku":"JER-002","name":"Jeringa 5ml","category":"Instrumental","unit_price":450,"unit_of_measure":"unidad","supplier_id":1}'
```

**Respuesta exitosa (201):**
```json
{
  "id": 15,
  "sku": "JER-002",
  "name": "Jeringa 5ml",
  "category": "Instrumental",
  "unit_price": 450.00,
  "unit_of_measure": "unidad",
  "supplier_id": 1,
  "is_active": true,
  "created_at": "2025-11-02T10:30:00Z"
}
```

### `GET /products/{product_id}`
Obtiene detalle completo de un producto por ID.

**Path Parameters:**
- `product_id`: ID numérico del producto (required)

**Ejemplo:**
```bash
curl "http://localhost:3001/products/12"
```

### `PUT /products/{product_id}`
Actualizar un producto existente.

**Path Parameters:**
- `product_id`: ID numérico del producto (required)

**Request Body:** Mismo formato que POST, todos los campos opcionales.

**Ejemplo:**
```bash
curl -X PUT "http://localhost:3001/products/12" \
  -H "Content-Type: application/json" \
  -d '{"unit_price": 380.00, "description": "Jeringa actualizada"}'
```

### `DELETE /products/{product_id}`
Eliminar (desactivar) un producto.

**Path Parameters:**
- `product_id`: ID numérico del producto (required)

**Query Parameters:**
- `hard_delete`: true/false (default: false) - Si es true, elimina permanentemente

**Ejemplos:**
```bash
# Soft delete (desactivar)
curl -X DELETE "http://localhost:3001/products/12"

# Hard delete (eliminar permanentemente)
curl -X DELETE "http://localhost:3001/products/12?hard_delete=true"
```

## Notas Importantes

### Diferencia entre Búsqueda por SKU vs Obtener por ID

**Búsqueda por SKU (Query Parameter):**
- Usar: `GET /products?sku=MED-2025-001`
- Devuelve: Lista de productos (array) que coincidan con el SKU
- Propósito: Búsqueda y filtrado

**Obtener por ID (Path Parameter):**
- Usar: `GET /products/12`
- Devuelve: Un producto específico (objeto) con información detallada
- Propósito: Operaciones CRUD precisas

### Convenciones de la API

- **IDs numéricos** se usan para operaciones CRUD (Create, Read, Update, Delete)
- **SKUs** se usan para búsquedas y filtros de negocio
- Los endpoints siguen el estándar REST con IDs para mayor estabilidad
- Soft delete es el comportamiento por defecto para preservar integridad referencial

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
# Ejecutar todos los tests con cobertura
pipenv run pytest --cov=src --cov-report=term-missing

# Ejecutar tests específicos de productos
pipenv run pytest tests/commands/ tests/blueprints/test_products_blueprint.py -v

# Ejecutar con reporte HTML de cobertura
pipenv run pytest --cov=src --cov-report=html
```

### Estado de Cobertura de Código

El proyecto mantiene **88% de cobertura total** con **157 tests** que validan exhaustivamente todas las operaciones CRUD de productos:

**Componentes con 100% de cobertura:**
- ✅ `CreateProduct` - 38 líneas (18 tests)
- ✅ `UpdateProduct` - 53 líneas (23 tests) 
- ✅ `DeleteProduct` - 34 líneas (18 tests)
- ✅ `GetProductById` - 14 líneas (10 tests)
- ✅ `GetProductBySku` - 12 líneas (9 tests)
- ✅ `GetProducts` - 37 líneas (12 tests)
- ✅ `Product` (modelo) - 46 líneas (9 tests)

**Tipos de pruebas implementadas:**
- ✨ Validación de datos y campos requeridos
- 🔍 Casos de error y excepciones personalizadas
- 💾 Operaciones de base de datos (CRUD completo)
- 🔄 Transacciones y rollbacks automáticos
- 📄 Validación de JSON y tipos de datos
- 🎯 Escenarios edge cases y límites

### Estructura de Tests

```
tests/
├── commands/           # Tests de lógica de negocio
│   ├── test_create_product.py              # 18 tests
│   ├── test_update_product.py              # 23 tests  
│   ├── test_delete_product.py              # 18 tests
│   ├── test_get_product_by_id.py           # 10 tests
│   ├── test_commands_get_product_by_sku.py # 9 tests
│   └── test_commands_get_products.py       # 12 tests
├── blueprints/         # Tests de endpoints REST
│   ├── test_products_blueprint.py          # 22 tests
│   └── test_blueprints_products.py         # 15 tests
├── models/             # Tests de modelos de datos
│   ├── test_models_product.py              # 9 tests
│   └── test_models_other.py                # 9 tests
└── errors/             # Tests de manejo de errores
    └── test_errors.py                      # 12 tests
```

### Ejemplos de Uso

```bash
# Health check
curl http://localhost:3001/health

# Health check específico de productos
curl http://localhost:3001/products/health

# Listar productos
curl http://localhost:3001/products

# Buscar por SKU (query parameter)
curl "http://localhost:3001/products?sku=JER-001"

# Obtener producto específico por ID
curl http://localhost:3001/products/1

# Crear producto
curl -X POST "http://localhost:3001/products" \
  -H "Content-Type: application/json" \
  -d '{"sku":"TEST-001","name":"Producto Test","category":"Test","unit_price":100,"unit_of_measure":"unidad","supplier_id":1}'

# Actualizar producto por ID
curl -X PUT "http://localhost:3001/products/15" \
  -H "Content-Type: application/json" \
  -d '{"unit_price": 120.00}'

# Eliminar producto por ID (soft delete)
curl -X DELETE "http://localhost:3001/products/15"

# Eliminar producto por ID (hard delete)
curl -X DELETE "http://localhost:3001/products/15?hard_delete=true"
```

## 📋 **Referencia Rápida - Endpoints CRUD**

| Método | Endpoint | Descripción | Códigos de Respuesta |
|--------|----------|-------------|---------------------|
| GET | `/products` | Listar productos con filtros | 200, 400, 500 |
| POST | `/products` | Crear nuevo producto | 201, 400, 500 |
| GET | `/products/{id}` | Obtener producto por ID | 200, 404, 500 |
| PUT | `/products/{id}` | Actualizar producto | 200, 400, 404, 500 |
| DELETE | `/products/{id}` | Eliminar producto | 200, 404, 500 |

### **Campos Requeridos para Crear Producto:**
- `sku` (string) - Identificador único
- `name` (string) - Nombre del producto  
- `category` (string) - Categoría
- `unit_price` (number) - Precio unitario
- `unit_of_measure` (string) - Unidad de medida
- `supplier_id` (integer) - ID del proveedor

### **Campos Opcionales:**
- `description`, `subcategory`, `currency`, `requires_cold_chain`
- `storage_temperature_min/max`, `storage_humidity_max`
- `sanitary_registration`, `requires_prescription`, `regulatory_class`
- `weight_kg`, `length_cm`, `width_cm`, `height_cm`
- `manufacturer`, `country_of_origin`, `barcode`, `image_url`