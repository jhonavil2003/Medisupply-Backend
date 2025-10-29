"""
Seed data script for sales-service development database.
Creates sample customers and orders for testing.
"""
import os
import sys
from datetime import datetime, timedelta
from decimal import Decimal

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.main import create_app
from src.session import db
from src.models.customer import Customer
from src.models.order import Order
from src.models.order_item import OrderItem

# Import shared seed data
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from shared_seed_data import CUSTOMERS_DATA, DISTRIBUTION_CENTERS_DATA, PRODUCTS_DATA, get_product_by_sku


def seed_customers():
    """Create sample customers."""
    print("👥 Creando clientes...")
    
    customers = []
    for customer_data in CUSTOMERS_DATA:
        customer = Customer(**customer_data)
        customers.append(customer)
        db.session.add(customer)
    
    db.session.commit()
    return customers


def seed_orders(customers):
    """Create sample orders with order items."""
    print("📦 Creando órdenes...")
    
    # Get distribution center codes
    dc_codes = [dc['code'] for dc in DISTRIBUTION_CENTERS_DATA]
    
    # Sample products for orders with realistic pricing
    order_products = [
        {'sku': 'JER-001', 'qty': 500, 'discount': 5.0},
        {'sku': 'JER-005', 'qty': 300, 'discount': 5.0},
        {'sku': 'GLV-LAT-M', 'qty': 50, 'discount': 10.0},
        {'sku': 'GLV-NIL-L', 'qty': 30, 'discount': 10.0},
        {'sku': 'MASK-N95', 'qty': 100, 'discount': 8.0},
        {'sku': 'GAUZE-10X10', 'qty': 200, 'discount': 5.0},
        {'sku': 'ALCO-500ML', 'qty': 100, 'discount': 0.0},
        {'sku': 'BAND-ELAS-5CM', 'qty': 150, 'discount': 5.0},
    ]
    
    # Order configurations with complete data
    orders_data = [
        {
            "order_number": "ORD-2024-001",
            "seller_id": "SELLER-001",
            "customer_idx": 0,
            "delivery_address": "Carrera 7 No. 40-62",
            "delivery_city": "Bogotá",
            "delivery_department": "Cundinamarca",
            "preferred_distribution_center": dc_codes[0],  # CEDIS-BOG
            "payment_method": "Crédito 60 días",
            "notes": "Entrega urgente - Hospital principal",
            "days_offset": 0,
            "products": [
                {'sku': 'JER-001', 'qty': 500, 'discount': 5.0},
                {'sku': 'GLV-LAT-M', 'qty': 50, 'discount': 10.0},
                {'sku': 'MASK-N95', 'qty': 100, 'discount': 8.0},
            ]
        },
        {
            "order_number": "ORD-2024-002",
            "seller_id": "SELLER-002",
            "customer_idx": 1,
            "delivery_address": "Calle 134 No. 7B-83",
            "delivery_city": "Bogotá",
            "delivery_department": "Cundinamarca",
            "preferred_distribution_center": dc_codes[0],  # CEDIS-BOG
            "payment_method": "Crédito 45 días",
            "notes": "Verificar certificados antes de envío",
            "days_offset": 1,
            "products": [
                {'sku': 'JER-005', 'qty': 300, 'discount': 5.0},
                {'sku': 'GAUZE-10X10', 'qty': 200, 'discount': 5.0},
            ]
        },
        {
            "order_number": "ORD-2024-003",
            "seller_id": "SELLER-001",
            "customer_idx": 2,
            "delivery_address": "Carrera 15 No. 88-64",
            "delivery_city": "Bogotá",
            "delivery_department": "Cundinamarca",
            "preferred_distribution_center": dc_codes[0],  # CEDIS-BOG
            "payment_method": "Crédito 30 días",
            "notes": "Cliente preferencial - máxima prioridad",
            "days_offset": 2,
            "products": [
                {'sku': 'ALCO-500ML', 'qty': 100, 'discount': 0.0},
                {'sku': 'BAND-ELAS-5CM', 'qty': 150, 'discount': 5.0},
                {'sku': 'GLV-NIL-L', 'qty': 30, 'discount': 10.0},
            ]
        },
        {
            "order_number": "ORD-2024-004",
            "seller_id": "SELLER-003",
            "customer_idx": 3,
            "delivery_address": "Calle 5 No. 38-71",
            "delivery_city": "Cali",
            "delivery_department": "Valle del Cauca",
            "preferred_distribution_center": dc_codes[2],  # CEDIS-CALI
            "payment_method": "Crédito 60 días",
            "notes": "Requiere factura electrónica",
            "days_offset": 3,
            "products": [
                {'sku': 'JER-001', 'qty': 400, 'discount': 5.0},
                {'sku': 'JER-005', 'qty': 200, 'discount': 5.0},
                {'sku': 'MASK-N95', 'qty': 80, 'discount': 8.0},
            ]
        },
        {
            "order_number": "ORD-2024-005",
            "seller_id": "SELLER-002",
            "customer_idx": 4,
            "delivery_address": "Calle 78B No. 69-240",
            "delivery_city": "Medellín",
            "delivery_department": "Antioquia",
            "preferred_distribution_center": dc_codes[1],  # CEDIS-MED
            "payment_method": "Crédito 90 días",
            "notes": "Primera orden del año - seguimiento especial",
            "days_offset": 4,
            "products": [
                {'sku': 'GLV-LAT-M', 'qty': 100, 'discount': 12.0},
                {'sku': 'GLV-NIL-L', 'qty': 80, 'discount': 12.0},
                {'sku': 'GAUZE-10X10', 'qty': 300, 'discount': 5.0},
                {'sku': 'ALCO-500ML', 'qty': 50, 'discount': 0.0},
            ]
        }
    ]
    
    orders_created = []
    for order_data in orders_data:
        # Create order date (spreading orders over days)
        order_date = datetime.now() - timedelta(days=order_data["days_offset"])
        
        # Create order
        order = Order(
            order_number=order_data["order_number"],
            order_date=order_date,
            seller_id=order_data["seller_id"],
            customer_id=customers[order_data["customer_idx"]].id,
            delivery_address=order_data["delivery_address"],
            delivery_city=order_data["delivery_city"],
            delivery_department=order_data["delivery_department"],
            preferred_distribution_center=order_data["preferred_distribution_center"],
            payment_method=order_data["payment_method"],
            notes=order_data["notes"],
            subtotal=Decimal('0.0'),
            discount_amount=Decimal('0.0'),
            tax_amount=Decimal('0.0'),
            total_amount=Decimal('0.0')
        )
        
        # Add order items from the order configuration
        order_subtotal = Decimal('0.0')
        order_discount = Decimal('0.0')
        order_tax = Decimal('0.0')
        
        for product_info in order_data["products"]:
            product_data = get_product_by_sku(product_info['sku'])
            if not product_data:
                continue
            
            quantity = product_info['qty']
            unit_price = product_data['unit_price']
            discount_pct = Decimal(str(product_info['discount']))
            
            # Calculate item totals
            item_subtotal = Decimal(str(quantity)) * unit_price
            item_discount = item_subtotal * (discount_pct / Decimal('100'))
            item_after_discount = item_subtotal - item_discount
            item_tax = item_after_discount * Decimal('0.19')  # 19% IVA
            item_total = item_after_discount + item_tax
            
            order_item = OrderItem(
                product_sku=product_data['sku'],
                product_name=product_data['name'],
                quantity=quantity,
                unit_price=float(unit_price),
                discount_percentage=float(discount_pct),
                discount_amount=float(item_discount),
                tax_percentage=19.0,
                tax_amount=float(item_tax),
                subtotal=float(item_after_discount),
                total=float(item_total),
                distribution_center_code=order_data["preferred_distribution_center"]
            )
            order.items.append(order_item)
            
            order_subtotal += item_subtotal
            order_discount += item_discount
            order_tax += item_tax
        
        # Update order totals
        order.subtotal = float(order_subtotal)
        order.discount_amount = float(order_discount)
        order.tax_amount = float(order_tax)
        order.total_amount = float(order_subtotal - order_discount + order_tax)
        
        db.session.add(order)
        orders_created.append(order)
    
    db.session.commit()
    return orders_created


def main():
    """Main function to seed the database."""
    print("🌱 Iniciando seed de datos...")
    
    app = create_app()
    
    with app.app_context():
        print("🗑️  Clearing existing data...")
        db.drop_all()
        db.create_all()
        
        # Seed customers
        customers = seed_customers()
        print(f"✅ Creados {len(customers)} clientes")
        
        # Seed orders
        orders = seed_orders(customers)
        print(f"✅ Creadas {len(orders)} órdenes")
        
        print("\n📊 Resumen de datos:")
        print(f"  Clientes: {len(customers)}")
        print(f"  Órdenes: {len(orders)}")
        total_items = sum(len(list(order.items)) for order in orders)
        print(f"  Items de orden: {total_items}")
        
        # Show order summary
        print("\n📦 Resumen de órdenes:")
        for order in orders:
            print(f"  {order.order_number}: {len(list(order.items))} items, Total: ${order.total_amount:,.2f}")
        
        print("\n✅ Seed completado exitosamente!")


if __name__ == '__main__':
    main()
