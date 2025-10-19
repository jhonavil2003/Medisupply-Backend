"""
Seed data script for sales-service development database.
Creates sample customers and orders for testing.
"""
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.main import create_app
from src.session import db
from src.models.customer import Customer
from src.models.order import Order
from src.models.order_item import OrderItem


def seed_customers():
    """Create sample customers."""
    customers_data = [
        {
            'document_type': 'NIT',
            'document_number': '900123456-1',
            'business_name': 'Hospital Universitario San Ignacio',
            'trade_name': 'Hospital San Ignacio',
            'customer_type': 'hospital',
            'contact_name': 'María González',
            'contact_email': 'compras@hospitalsanignacio.com',
            'contact_phone': '+57 1 5946161',
            'address': 'Carrera 7 No. 40-62',
            'city': 'Bogotá',
            'department': 'Cundinamarca',
            'country': 'Colombia',
            'credit_limit': 50000000.00,
            'credit_days': 60,
            'is_active': True
        },
        {
            'document_type': 'NIT',
            'document_number': '800234567-2',
            'business_name': 'Clínica El Bosque',
            'trade_name': 'Clínica El Bosque',
            'customer_type': 'clinica',
            'contact_name': 'Carlos Ramírez',
            'contact_email': 'compras@clinicaelbosque.com',
            'contact_phone': '+57 1 6489000',
            'address': 'Calle 134 No. 7B-83',
            'city': 'Bogotá',
            'department': 'Cundinamarca',
            'country': 'Colombia',
            'credit_limit': 30000000.00,
            'credit_days': 45,
            'is_active': True
        },
        {
            'document_type': 'NIT',
            'document_number': '890345678-3',
            'business_name': 'Farmacias Cruz Verde S.A.',
            'trade_name': 'Cruz Verde',
            'customer_type': 'farmacia',
            'contact_name': 'Ana López',
            'contact_email': 'compras@cruzverde.com.co',
            'contact_phone': '+57 1 7428000',
            'address': 'Carrera 15 No. 88-64',
            'city': 'Bogotá',
            'department': 'Cundinamarca',
            'country': 'Colombia',
            'credit_limit': 20000000.00,
            'credit_days': 30,
            'is_active': True
        },
        {
            'document_type': 'NIT',
            'document_number': '890456789-4',
            'business_name': 'Distribuciones Médicas del Valle S.A.S',
            'trade_name': 'Dismeva',
            'customer_type': 'distribuidor',
            'contact_name': 'Jorge Martínez',
            'contact_email': 'ventas@dismeva.com',
            'contact_phone': '+57 2 3331234',
            'address': 'Calle 5 No. 38-71',
            'city': 'Cali',
            'department': 'Valle del Cauca',
            'country': 'Colombia',
            'credit_limit': 40000000.00,
            'credit_days': 60,
            'is_active': True
        },
        {
            'document_type': 'NIT',
            'document_number': '890567890-5',
            'business_name': 'Hospital Pablo Tobón Uribe',
            'trade_name': 'Hospital Pablo Tobón',
            'customer_type': 'hospital',
            'contact_name': 'Laura Sánchez',
            'contact_email': 'compras@hptu.org.co',
            'contact_phone': '+57 4 4459000',
            'address': 'Calle 78B No. 69-240',
            'city': 'Medellín',
            'department': 'Antioquia',
            'country': 'Colombia',
            'credit_limit': 60000000.00,
            'credit_days': 90,
            'is_active': True
        }
    ]
    
    customers = []
    for data in customers_data:
        customer = Customer(**data)
        customers.append(customer)
        db.session.add(customer)
    
    db.session.commit()
    return customers


def seed_orders(customers):
    """Create sample orders with order items."""
    print("📦 Creando órdenes...")
    
    # Order configurations with complete data
    orders_data = [
        {
            "order_number": "ORD-2024-001",
            "seller_id": "SELLER-001",
            "customer": customers[0],
            "delivery_address": "Calle 100 #15-20",
            "delivery_city": "Bogotá",
            "delivery_department": "Cundinamarca",
            "preferred_distribution_center": "CEDIS-BOG",
            "payment_method": "Crédito 30 días",
            "notes": "Entrega urgente - Hospital principal",
            "days_offset": 0
        },
        {
            "order_number": "ORD-2024-002",
            "seller_id": "SELLER-002",
            "customer": customers[1],
            "delivery_address": "Carrera 50 #70-80",
            "delivery_city": "Medellín",
            "delivery_department": "Antioquia",
            "preferred_distribution_center": "CEDIS-MED",
            "payment_method": "Contado",
            "notes": "Verificar certificados antes de envío",
            "days_offset": 1
        },
        {
            "order_number": "ORD-2024-003",
            "seller_id": "SELLER-001",
            "customer": customers[2],
            "delivery_address": "Avenida 6 Norte #25-30",
            "delivery_city": "Cali",
            "delivery_department": "Valle del Cauca",
            "preferred_distribution_center": "CEDIS-CALI",
            "payment_method": "Crédito 60 días",
            "notes": "Cliente preferencial - máxima prioridad",
            "days_offset": 2
        },
        {
            "order_number": "ORD-2024-004",
            "seller_id": "SELLER-003",
            "customer": customers[3],
            "delivery_address": "Calle 85 #48-10",
            "delivery_city": "Barranquilla",
            "delivery_department": "Atlántico",
            "preferred_distribution_center": "CEDIS-BAQ",
            "payment_method": "Crédito 30 días",
            "notes": "Requiere factura electrónica",
            "days_offset": 3
        },
        {
            "order_number": "ORD-2024-005",
            "seller_id": "SELLER-002",
            "customer": customers[4],
            "delivery_address": "Carrera 27 #10-20",
            "delivery_city": "Bucaramanga",
            "delivery_department": "Santander",
            "preferred_distribution_center": "CEDIS-BOG",
            "payment_method": "Contado",
            "notes": "Primera orden del cliente - seguimiento especial",
            "days_offset": 4
        }
    ]
    
    orders_created = []
    for order_data in orders_data:
        # Create order date (spreading orders over 5 days)
        order_date = datetime.now() - timedelta(days=order_data["days_offset"])
        
        # Create order
        order = Order(
            order_number=order_data["order_number"],
            order_date=order_date,
            seller_id=order_data["seller_id"],
            customer_id=order_data["customer"].id,
            delivery_address=order_data["delivery_address"],
            delivery_city=order_data["delivery_city"],
            delivery_department=order_data["delivery_department"],
            preferred_distribution_center=order_data["preferred_distribution_center"],
            payment_method=order_data["payment_method"],
            notes=order_data["notes"],
            subtotal=0.0,
            discount_amount=0.0,
            tax_amount=0.0,
            total_amount=0.0
        )
        
        # Add order item with product JER-001 (Jeringa)
        quantity = 50
        unit_price = 1500.0
        item_subtotal = quantity * unit_price
        item_discount = item_subtotal * 0.05  # 5% discount
        item_after_discount = item_subtotal - item_discount
        item_tax = item_after_discount * 0.19  # 19% IVA
        item_total = item_after_discount + item_tax
        
        order_item = OrderItem(
            product_sku="JER-001",
            product_name="Jeringa desechable 5ml",
            quantity=quantity,
            unit_price=unit_price,
            discount_percentage=5.0,
            discount_amount=item_discount,
            tax_percentage=19.0,
            tax_amount=item_tax,
            subtotal=item_after_discount,
            total=item_total,
            distribution_center_code=order_data["preferred_distribution_center"]
        )
        order.items.append(order_item)
        
        # Update order totals
        order.subtotal = item_subtotal
        order.discount_amount = item_discount
        order.tax_amount = item_tax
        order.total_amount = item_total
        
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
        print("👥 Creando clientes...")
        customers = seed_customers()
        print(f"✅ Creados {len(customers)} clientes")
        
        # Seed orders
        orders = seed_orders(customers)
        print(f"✅ Creadas {len(orders)} órdenes")
        
        print("\n📊 Resumen de datos:")
        print(f"  Clientes: {len(customers)}")
        print(f"  Órdenes: {len(orders)}")
        print("\n✅ Seed completado exitosamente!")


if __name__ == '__main__':
    main()
