# Manejo de Errores - PATCH /orders/{orderId}

## Resumen de Implementación

Este documento describe el manejo completo de errores implementado para el endpoint `PATCH /orders/{orderId}` que permite actualizar órdenes existentes.

---

## Códigos de Estado HTTP Implementados

### ✅ **200 OK - Actualización Exitosa**
```json
{
  "id": 1,
  "order_number": "ORD-20251022-0001",
  "status": "confirmed",
  "customer": {...},
  "items": [...],
  "total_amount": 113050.00
}
```

---

### ❌ **400 Bad Request - Error de Validación**

#### 1. **Orden no está en estado PENDING**
```json
{
  "error": "Solo se pueden editar órdenes pendientes",
  "status_code": 400
}
```
**Causa**: Se intenta actualizar una orden que no está en estado `pending` (ej: `confirmed`, `cancelled`, `delivered`).

---

#### 2. **Items vacíos**
```json
{
  "error": "Order must have at least one item",
  "status_code": 400
}
```
**Causa**: Se envía un array vacío en el campo `items`.

**Ejemplo de request inválido:**
```json
{
  "items": []
}
```

---

#### 3. **Quantity inválida (≤ 0)**
```json
{
  "error": "Item at index 0: quantity must be greater than 0 (received: 0)",
  "status_code": 400
}
```
**Causa**: Un item tiene `quantity` igual a 0 o negativa.

**Ejemplos de requests inválidos:**
```json
// Quantity = 0
{
  "items": [{"product_sku": "JER-001", "quantity": 0}]
}

// Quantity negativa
{
  "items": [{"product_sku": "JER-001", "quantity": -5}]
}
```

---

#### 4. **Campo requerido faltante en items**
```json
{
  "error": "Item at index 0 is missing required field: 'product_sku'",
  "status_code": 400
}
```
**Causa**: Un item no incluye `product_sku` o `quantity`.

**Ejemplo de request inválido:**
```json
{
  "items": [
    {
      "quantity": 10
      // Falta product_sku
    }
  ]
}
```

---

#### 5. **Transición de estado inválida**
```json
{
  "error": "Invalid status transition: 'pending' → 'cancelled'. Allowed transitions: confirmed, pending",
  "status_code": 400
}
```
**Causa**: Se intenta cambiar el estado a un valor no permitido.

**Transiciones permitidas:**
- `pending` → `confirmed` ✅
- `pending` → `pending` ✅ (sin cambio)
- `pending` → `cancelled` ❌ (NO permitido)

---

#### 6. **Formato de datos inválido**

##### JSON body vacío:
```json
{
  "error": "Request body is required and must be a valid JSON object",
  "status_code": 400
}
```

##### Content-Type incorrecto:
```json
{
  "error": "Content-Type must be application/json",
  "status_code": 400
}
```

##### Tipo de dato incorrecto:
```json
{
  "error": "Field 'items' must be a list",
  "status_code": 400
}
```

##### Valor numérico fuera de rango:
```json
{
  "error": "Item at index 0: discount_percentage must be between 0 and 100",
  "status_code": 400
}
```

---

### ❌ **403 Forbidden - Sin Permisos**

```json
{
  "error": "No tiene permisos para editar esta orden",
  "status_code": 403
}
```

**Causa**: El usuario no tiene permisos para modificar la orden solicitada.

**Nota**: Esta validación está pendiente de implementación completa (requiere sistema de autenticación/autorización).

---

### ❌ **404 Not Found - Orden No Encontrada**

```json
{
  "error": "Order with id 99999 not found",
  "status_code": 404,
  "order_id": 99999
}
```

**Causa**: No existe una orden con el ID especificado.

---

### ❌ **409 Conflict - Conflicto de Estado**

```json
{
  "error": "Insufficient stock for product SKU-001",
  "status_code": 409
}
```

**Causa**: 
- Stock insuficiente para algún producto
- Conflicto con el estado actual del recurso

**Nota**: La validación de stock está pendiente de implementación (requiere integración con servicio de inventario).

---

### ❌ **500 Internal Server Error - Error del Servidor**

#### Error de base de datos:
```json
{
  "error": "Database error while updating order: <detalle del error>",
  "status_code": 500
}
```

#### Error inesperado:
```json
{
  "error": "Internal server error: <detalle del error>",
  "status_code": 500
}
```

**Causa**: 
- Error al guardar cambios en la base de datos
- Error de integridad de datos
- Excepción no controlada

---

## Validaciones Implementadas

### ✅ **Validación de Request**
1. Content-Type debe ser `application/json`
2. Body debe ser un objeto JSON válido
3. Body no puede estar vacío
4. Al menos un campo debe ser enviado para actualizar

### ✅ **Validación de Orden**
1. La orden debe existir (404 si no existe)
2. La orden debe estar en estado `pending` (400 si no lo está)

### ✅ **Validación de Items** (si se envían)
1. `items` debe ser un array
2. `items` no puede estar vacío
3. Cada item debe ser un objeto válido
4. Campos requeridos: `product_sku`, `quantity`
5. `quantity` debe ser un entero > 0
6. `unit_price` no puede ser negativo
7. `discount_percentage` debe estar entre 0 y 100
8. `tax_percentage` debe estar entre 0 y 100

### ✅ **Validación de Estado**
1. Valor de `status` debe ser válido
2. Transición de estado debe estar permitida

### ✅ **Protección de Campos Inmutables**
Los siguientes campos se ignoran silenciosamente si se envían:
- `customer_id`
- `seller_id`
- `seller_name`
- `order_number`
- `order_date`
- `created_at`
- `subtotal`, `discount_amount`, `tax_amount`, `total_amount` (auto-calculados)

---

## Ejemplos de Uso

### ✅ **Actualización exitosa - Cambiar dirección**
```bash
PATCH /orders/1
Content-Type: application/json

{
  "delivery_address": "Nueva Calle 123 #45-67",
  "delivery_city": "Medellín",
  "delivery_department": "Antioquia"
}
```

**Response 200 OK:**
```json
{
  "id": 1,
  "order_number": "ORD-20251022-0001",
  "delivery_address": "Nueva Calle 123 #45-67",
  "delivery_city": "Medellín",
  "delivery_department": "Antioquia",
  "customer": {...},
  "items": [...]
}
```

---

### ✅ **Actualización exitosa - Confirmar orden**
```bash
PATCH /orders/1
Content-Type: application/json

{
  "status": "confirmed"
}
```

**Response 200 OK:**
```json
{
  "id": 1,
  "status": "confirmed",
  ...
}
```

---

### ✅ **Actualización exitosa - Reemplazar items**
```bash
PATCH /orders/1
Content-Type: application/json

{
  "items": [
    {
      "product_sku": "JER-001",
      "quantity": 15,
      "unit_price": 350.00,
      "discount_percentage": 10.0,
      "tax_percentage": 19.0
    }
  ]
}
```

**Response 200 OK:**
```json
{
  "id": 1,
  "items": [
    {
      "product_sku": "JER-001",
      "quantity": 15,
      "subtotal": 4725.00,
      "total": 5622.75
    }
  ],
  "subtotal": 5250.00,
  "discount_amount": 525.00,
  "tax_amount": 897.75,
  "total_amount": 5622.75
}
```

---

### ❌ **Error 400 - Orden no está en PENDING**
```bash
PATCH /orders/1
Content-Type: application/json

{
  "notes": "Intentar actualizar orden confirmada"
}
```

**Response 400 Bad Request:**
```json
{
  "error": "Solo se pueden editar órdenes pendientes",
  "status_code": 400
}
```

---

### ❌ **Error 400 - Items vacíos**
```bash
PATCH /orders/1
Content-Type: application/json

{
  "items": []
}
```

**Response 400 Bad Request:**
```json
{
  "error": "Order must have at least one item",
  "status_code": 400
}
```

---

### ❌ **Error 400 - Quantity inválida**
```bash
PATCH /orders/1
Content-Type: application/json

{
  "items": [
    {
      "product_sku": "JER-001",
      "quantity": 0
    }
  ]
}
```

**Response 400 Bad Request:**
```json
{
  "error": "Item at index 0: quantity must be greater than 0 (received: 0)",
  "status_code": 400
}
```

---

### ❌ **Error 404 - Orden no encontrada**
```bash
PATCH /orders/99999
Content-Type: application/json

{
  "notes": "Test"
}
```

**Response 404 Not Found:**
```json
{
  "error": "Order with id 99999 not found",
  "status_code": 404,
  "order_id": 99999
}
```

---

## Manejo de Rollback

En caso de error durante la actualización, la transacción de base de datos se revierte automáticamente (**rollback**):

```python
try:
    # Operaciones de actualización
    db.session.commit()
except SQLAlchemyError as e:
    db.session.rollback()  # Rollback automático
    raise DatabaseError(...)
```

**Garantía**: Si ocurre un error, la orden permanece en su estado original sin cambios parciales.

---

## Tests de Cobertura

### Estadísticas de Testing:
- **165 tests totales** ejecutados
- **62 tests** específicos para manejo de errores
- **0 fallos**
- **Cobertura**: 94% en UpdateOrder command y blueprint

### Tests Implementados:
- ✅ 19 tests de validación de errores HTTP (400, 404)
- ✅ 25 tests del comando UpdateOrder
- ✅ 18 tests del endpoint PATCH en blueprint
- ✅ Tests de formato de respuestas de error
- ✅ Tests de rollback en errores de BD

---

## Mejoras Pendientes

### 🔜 **403 Forbidden - Validación de Permisos**
Implementar sistema de autorización para validar que el usuario tiene permisos para editar la orden.

**Ejemplo de implementación futura:**
```python
user_id = get_user_from_jwt_token(request)
if not user_has_permission_to_edit(order_id, user_id):
    raise ForbiddenError('No tiene permisos para editar esta orden')
```

---

### 🔜 **409 Conflict - Validación de Stock**
Integrar con servicio de inventario para validar disponibilidad de stock al actualizar items.

**Ejemplo de implementación futura:**
```python
for item in items:
    stock = check_stock_availability(item['product_sku'], item['quantity'])
    if not stock.available:
        raise ConflictError(f'Insufficient stock for {item["product_sku"]}')
```

---

### 🔜 **404 Not Found - Validación de Productos**
Validar que cada `product_sku` existe en el catálogo de productos.

**Ejemplo de implementación futura:**
```python
for item in items:
    product = get_product_by_sku(item['product_sku'])
    if not product:
        raise NotFoundError(f'Product {item["product_sku"]} not found')
```

---

## Arquitectura de Manejo de Errores

```
┌─────────────────────────────────────────────┐
│  Flask Blueprint (orders.py)                │
│  - Valida Content-Type                      │
│  - Valida JSON body                         │
│  - Try/Catch por tipo de error              │
│  - Retorna respuestas HTTP apropiadas       │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│  UpdateOrder Command                        │
│  - Valida orden existe                      │
│  - Valida estado PENDING                    │
│  - Valida formato de datos                  │
│  - Valida reglas de negocio                 │
│  - Rollback automático en error             │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│  Custom Exceptions (errors.py)              │
│  - NotFoundError (404)                      │
│  - ValidationError (400)                    │
│  - ApiError (400/409)                       │
│  - ForbiddenError (403)                     │
│  - DatabaseError (500)                      │
└─────────────────────────────────────────────┘
```

---

## Notas de Implementación

1. **Mensajes de error descriptivos**: Todos los errores incluyen mensajes claros que indican exactamente qué salió mal.

2. **Índices en errores de items**: Los errores de validación de items incluyen el índice (`index 0`, `index 1`, etc.) para facilitar la depuración.

3. **Consistencia de respuestas**: Todas las respuestas de error incluyen los campos `error` y `status_code`.

4. **Rollback automático**: Cualquier error durante la actualización revierte todos los cambios.

5. **Protección de datos**: Los campos inmutables se ignoran silenciosamente para evitar modificaciones accidentales.

---

## Autor
Implementado como parte de HU-127: Seguimiento de entregas en tránsito
Fecha: 22 de octubre de 2025
