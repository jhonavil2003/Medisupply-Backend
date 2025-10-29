# Ejemplos de Uso - Endpoint PATCH /orders/{order_id}

## 📋 Endpoint
```
PATCH /orders/{order_id}
Content-Type: application/json
```

---

## ✅ Casos de Uso Exitosos

### 1️⃣ **Actualizar Dirección de Entrega**

**Request:**
```bash
curl -X PATCH http://localhost:3003/orders/1 \
  -H "Content-Type: application/json" \
  -d '{
    "delivery_address": "Calle 123 #45-67",
    "delivery_city": "Medellín",
    "delivery_department": "Antioquia",
    "notes": "Entrega urgente - horario 8am-12pm"
  }'
```

**Response: 200 OK**
```json
{
  "id": 1,
  "order_number": "ORD-20251023-0001",
  "customer_id": 1,
  "seller_id": "SELLER-001",
  "seller_name": "Juan Pérez",
  "order_date": "2025-10-23T10:30:00.000Z",
  "status": "pending",
  "subtotal": 100000.0,
  "discount_amount": 5000.0,
  "tax_amount": 18050.0,
  "total_amount": 113050.0,
  "payment_terms": "credito_30",
  "payment_method": "transferencia",
  "delivery_address": "Calle 123 #45-67",
  "delivery_city": "Medellín",
  "delivery_department": "Antioquia",
  "delivery_date": null,
  "preferred_distribution_center": "CEDIS-BOG",
  "notes": "Entrega urgente - horario 8am-12pm",
  "created_at": "2025-10-23T10:30:00.000Z",
  "updated_at": "2025-10-23T11:45:00.000Z",
  "items": [...],
  "customer": {...}
}
```

---

### 2️⃣ **Actualizar Términos de Pago**

**Request:**
```bash
curl -X PATCH http://localhost:3003/orders/1 \
  -H "Content-Type: application/json" \
  -d '{
    "payment_terms": "credito_45",
    "payment_method": "cheque"
  }'
```

**Response: 200 OK**
```json
{
  "id": 1,
  "payment_terms": "credito_45",
  "payment_method": "cheque",
  "updated_at": "2025-10-23T11:50:00.000Z",
  ...
}
```

---

### 3️⃣ **Confirmar Orden (Cambiar Estado)**

**Request:**
```bash
curl -X PATCH http://localhost:3003/orders/1 \
  -H "Content-Type: application/json" \
  -d '{
    "status": "confirmed"
  }'
```

**Response: 200 OK**
```json
{
  "id": 1,
  "status": "confirmed",
  "updated_at": "2025-10-23T12:00:00.000Z",
  ...
}
```

---

### 4️⃣ **Actualizar Items de la Orden (Reemplaza Completamente)**

**Request:**
```bash
curl -X PATCH http://localhost:3003/orders/1 \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {
        "product_sku": "JER-001",
        "product_name": "Jeringa desechable 3ml",
        "quantity": 150,
        "unit_price": 350.0,
        "discount_percentage": 10.0,
        "tax_percentage": 19.0
      },
      {
        "product_sku": "MASK-N95",
        "product_name": "Mascarilla N95",
        "quantity": 50,
        "unit_price": 5000.0,
        "discount_percentage": 0.0,
        "tax_percentage": 19.0
      }
    ]
  }'
```

**Response: 200 OK**
```json
{
  "id": 1,
  "order_number": "ORD-20251023-0001",
  "subtotal": 302500.0,
  "discount_amount": 5250.0,
  "tax_amount": 56437.5,
  "total_amount": 353687.5,
  "updated_at": "2025-10-23T12:15:00.000Z",
  "items": [
    {
      "id": 5,
      "order_id": 1,
      "product_sku": "JER-001",
      "product_name": "Jeringa desechable 3ml",
      "quantity": 150,
      "unit_price": 350.0,
      "discount_percentage": 10.0,
      "discount_amount": 5250.0,
      "tax_percentage": 19.0,
      "tax_amount": 9487.5,
      "subtotal": 47250.0,
      "total": 56737.5,
      "distribution_center_code": "CEDIS-BOG",
      "stock_confirmed": false,
      "created_at": "2025-10-23T12:15:00.000Z"
    },
    {
      "id": 6,
      "order_id": 1,
      "product_sku": "MASK-N95",
      "product_name": "Mascarilla N95",
      "quantity": 50,
      "unit_price": 5000.0,
      "discount_percentage": 0.0,
      "discount_amount": 0.0,
      "tax_percentage": 19.0,
      "tax_amount": 47500.0,
      "subtotal": 250000.0,
      "total": 297500.0,
      "distribution_center_code": "CEDIS-BOG",
      "stock_confirmed": false,
      "created_at": "2025-10-23T12:15:00.000Z"
    }
  ],
  "customer": {...}
}
```

---

### 5️⃣ **Actualización Parcial (Solo un Campo)**

**Request:**
```bash
curl -X PATCH http://localhost:3003/orders/1 \
  -H "Content-Type: application/json" \
  -d '{
    "notes": "Cliente solicita llamar antes de entregar"
  }'
```

**Response: 200 OK**
```json
{
  "id": 1,
  "notes": "Cliente solicita llamar antes de entregar",
  "updated_at": "2025-10-23T12:20:00.000Z",
  ...
}
```

---

## ❌ Casos de Error

### 1️⃣ **404 - Orden No Existe**

**Request:**
```bash
curl -X PATCH http://localhost:3003/orders/99999 \
  -H "Content-Type: application/json" \
  -d '{"notes": "Test"}'
```

**Response: 404 Not Found**
```json
{
  "error": "Order with id 99999 not found",
  "status_code": 404
}
```

---

### 2️⃣ **400 - Orden No Está en PENDING**

**Request:**
```bash
curl -X PATCH http://localhost:3003/orders/1 \
  -H "Content-Type: application/json" \
  -d '{"notes": "Try to update"}'
```

**Response: 400 Bad Request**
```json
{
  "error": "Solo se pueden editar órdenes pendientes",
  "status_code": 400
}
```

---

### 3️⃣ **400 - Transición de Estado Inválida**

**Request:**
```bash
curl -X PATCH http://localhost:3003/orders/1 \
  -H "Content-Type: application/json" \
  -d '{
    "status": "cancelled"
  }'
```

**Response: 400 Bad Request**
```json
{
  "error": "Invalid status transition: 'pending' → 'cancelled'. Allowed transitions: confirmed, pending",
  "status_code": 400
}
```

---

### 4️⃣ **400 - Items Vacíos**

**Request:**
```bash
curl -X PATCH http://localhost:3003/orders/1 \
  -H "Content-Type: application/json" \
  -d '{
    "items": []
  }'
```

**Response: 400 Bad Request**
```json
{
  "error": "Order must have at least one item",
  "status_code": 400
}
```

---

### 5️⃣ **400 - Quantity Inválida**

**Request:**
```bash
curl -X PATCH http://localhost:3003/orders/1 \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {
        "product_sku": "JER-001",
        "quantity": 0,
        "unit_price": 350.0
      }
    ]
  }'
```

**Response: 400 Bad Request**
```json
{
  "error": "Item quantity must be greater than 0",
  "status_code": 400
}
```

---

### 6️⃣ **400 - Campos Requeridos Faltantes**

**Request:**
```bash
curl -X PATCH http://localhost:3003/orders/1 \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {
        "quantity": 10,
        "unit_price": 350.0
      }
    ]
  }'
```

**Response: 400 Bad Request**
```json
{
  "error": "Item is missing required field: 'product_sku'",
  "status_code": 400
}
```

---

### 7️⃣ **400 - Request Body Vacío**

**Request:**
```bash
curl -X PATCH http://localhost:3003/orders/1 \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Response: 400 Bad Request**
```json
{
  "error": "Request body is required",
  "status_code": 400
}
```

---

## 🔒 Campos Inmutables (Ignorados Silenciosamente)

Estos campos **NO pueden modificarse** y serán ignorados si se envían en el request:

- `customer_id`
- `seller_id`
- `seller_name`
- `order_number`
- `order_date`
- `created_at`
- `subtotal` (auto-calculado)
- `discount_amount` (auto-calculado)
- `tax_amount` (auto-calculado)
- `total_amount` (auto-calculado)

**Ejemplo:**
```bash
curl -X PATCH http://localhost:3003/orders/1 \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": 999,
    "order_number": "FAKE-ORDER",
    "notes": "Update notes"
  }'
```

**Response: 200 OK** (customer_id y order_number son ignorados)
```json
{
  "id": 1,
  "customer_id": 1,
  "order_number": "ORD-20251023-0001",
  "notes": "Update notes",
  ...
}
```

---

## 📊 Campos Actualizables

### **Campos Simples:**
- `status` (solo PENDING → CONFIRMED)
- `payment_terms`
- `payment_method`
- `delivery_address`
- `delivery_city`
- `delivery_department`
- `preferred_distribution_center`
- `notes`

### **Campos Complejos:**
- `items` (lista completa - **reemplaza todos los items existentes**)

---

## 💡 Notas Importantes

1. **Actualización Parcial**: Solo los campos enviados en el request serán actualizados
2. **Items Replacement**: Si envías `items`, **todos** los items anteriores serán eliminados y reemplazados
3. **Recálculo Automático**: Los totales se recalculan automáticamente al actualizar items
4. **Solo PENDING**: Solo órdenes en estado `pending` pueden ser actualizadas
5. **Transiciones Permitidas**: `pending` → `confirmed` o mantener `pending`

---

## 🧪 Testing con cURL

```bash
# Variable para el ID de la orden
ORDER_ID=1

# 1. Actualizar dirección
curl -X PATCH http://localhost:3003/orders/$ORDER_ID \
  -H "Content-Type: application/json" \
  -d '{"delivery_address": "Nueva Calle 456"}'

# 2. Actualizar términos de pago
curl -X PATCH http://localhost:3003/orders/$ORDER_ID \
  -H "Content-Type: application/json" \
  -d '{"payment_terms": "credito_60"}'

# 3. Confirmar orden
curl -X PATCH http://localhost:3003/orders/$ORDER_ID \
  -H "Content-Type: application/json" \
  -d '{"status": "confirmed"}'

# 4. Ver orden actualizada
curl -X GET http://localhost:3003/orders/$ORDER_ID
```

---

## 🎯 Integración con App Móvil (Kotlin)

```kotlin
// Data classes
data class UpdateOrderRequest(
    val status: String? = null,
    val paymentTerms: String? = null,
    val paymentMethod: String? = null,
    val deliveryAddress: String? = null,
    val deliveryCity: String? = null,
    val deliveryDepartment: String? = null,
    val preferredDistributionCenter: String? = null,
    val notes: String? = null,
    val items: List<OrderItemRequest>? = null
)

data class OrderItemRequest(
    val productSku: String,
    val productName: String? = null,
    val quantity: Int,
    val unitPrice: Double? = null,
    val discountPercentage: Double? = null,
    val taxPercentage: Double? = null
)

// Retrofit Service
interface OrdersService {
    @PATCH("orders/{orderId}")
    suspend fun updateOrder(
        @Path("orderId") orderId: Int,
        @Body request: UpdateOrderRequest
    ): OrderResponse
}

// Uso
val updateRequest = UpdateOrderRequest(
    deliveryAddress = "Calle 123 #45-67",
    deliveryCity = "Medellín",
    notes = "Entrega urgente"
)

try {
    val updatedOrder = ordersService.updateOrder(orderId = 1, request = updateRequest)
    println("Orden actualizada: ${updatedOrder.orderNumber}")
} catch (e: HttpException) {
    when (e.code()) {
        400 -> println("Error de validación: ${e.message()}")
        404 -> println("Orden no encontrada")
        else -> println("Error: ${e.message()}")
    }
}
```
