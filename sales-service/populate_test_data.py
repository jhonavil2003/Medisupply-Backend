"""
Script para poblar la base de datos con datos de prueba coherentes para reportes.
Crea vendedores, clientes, productos, objetivos y órdenes con IDs consistentes.
"""
import sys
import os
from datetime import datetime, timedelta
from decimal import Decimal

# Agregar el directorio src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.session import db
from src.main import create_app
from src.entities.salesperson import Salesperson
from src.entities.salesperson_goal import SalespersonGoal, Region, Quarter, GoalType
from src.models.customer import Customer
from src.models.order import Order
from src.models.order_item import OrderItem

# Crear la aplicación
app = create_app()

def clear_test_data():
    """Elimina todos los datos de prueba existentes"""
    print("🗑️  Limpiando datos de prueba existentes...")
    
    with app.app_context():
        try:
            # Orden importante: primero items, luego orders, etc.
            OrderItem.query.delete()
            Order.query.delete()
            SalespersonGoal.query.delete()
            # No borramos salespersons ni customers para mantener IDs existentes
            
            db.session.commit()
            print("✅ Datos de prueba eliminados")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error limpiando datos: {e}")
            raise

def create_salesperson_goals():
    """Crea objetivos de ventas para los vendedores existentes"""
    print("\n📊 Creando objetivos de ventas...")
    
    with app.app_context():
        # Obtener vendedores existentes
        salespersons = Salesperson.query.all()
        
        if not salespersons:
            print("⚠️  No hay vendedores. Primero crea vendedores desde la interfaz.")
            return
        
        print(f"   Encontrados {len(salespersons)} vendedores")
        
        # Productos de ejemplo (SKUs que usaremos en las órdenes)
        products = [
            'MED-001',  # Ibuprofeno
            'MED-002',  # Paracetamol
            'MED-003',  # Amoxicilina
        ]
        
        goals_created = 0
        
        for salesperson in salespersons:
            print(f"   → Vendedor: {salesperson.get_full_name()} (ID: {salesperson.employee_id})")
            
            # Crear objetivos para Q4 (octubre, noviembre, diciembre)
            for product_sku in products:
                # Objetivo de unidades
                goal_units = SalespersonGoal(
                    id_vendedor=salesperson.employee_id,
                    id_producto=product_sku,
                    region=Region.NORTE.value,
                    trimestre=Quarter.Q4.value,
                    valor_objetivo=200,  # 200 unidades
                    tipo=GoalType.UNIDADES.value
                )
                db.session.add(goal_units)
                goals_created += 1
                
                # Objetivo monetario
                goal_money = SalespersonGoal(
                    id_vendedor=salesperson.employee_id,
                    id_producto=product_sku,
                    region=Region.SUR.value,
                    trimestre=Quarter.Q4.value,
                    valor_objetivo=3000000,  # 3 millones de pesos
                    tipo=GoalType.MONETARIO.value
                )
                db.session.add(goal_money)
                goals_created += 1
        
        try:
            db.session.commit()
            print(f"✅ {goals_created} objetivos creados")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error creando objetivos: {e}")
            raise

def create_test_orders():
    """Crea órdenes de prueba con los vendedores e items correctos"""
    print("\n🛒 Creando órdenes de prueba...")
    
    with app.app_context():
        # Obtener vendedores existentes
        salespersons = Salesperson.query.all()
        if not salespersons:
            print("⚠️  No hay vendedores disponibles")
            return
        
        # Obtener clientes existentes
        customers = Customer.query.filter_by(is_active=True).all()
        if not customers:
            print("⚠️  No hay clientes disponibles. Primero crea clientes desde la interfaz.")
            return
        
        print(f"   Vendedores disponibles: {len(salespersons)}")
        print(f"   Clientes disponibles: {len(customers)}")
        
        # Productos con precios
        products = [
            {'sku': 'MED-001', 'name': 'Ibuprofeno 400mg x 30', 'price': 15000},
            {'sku': 'MED-002', 'name': 'Paracetamol 500mg x 100', 'price': 12000},
            {'sku': 'MED-003', 'name': 'Amoxicilina 500mg x 21', 'price': 25000},
        ]
        
        orders_created = 0
        
        # Crear órdenes para los últimos 30 días
        for i in range(15):  # 15 órdenes de prueba
            # Fecha aleatoria en los últimos 30 días
            days_ago = i * 2
            order_date = datetime.utcnow() - timedelta(days=days_ago)
            
            # Seleccionar vendedor y cliente
            salesperson = salespersons[i % len(salespersons)]
            customer = customers[i % len(customers)]
            
            # Crear orden
            order = Order(
                order_number=f'ORD-TEST-{datetime.utcnow().strftime("%Y%m%d")}-{i+1:04d}',
                customer_id=customer.id,
                order_date=order_date,
                seller_id=salesperson.employee_id,  # ⚠️ AQUÍ ESTÁ LA CLAVE!
                seller_name=salesperson.get_full_name(),
                status='confirmed',
                payment_terms='credito',
                customer_document_number=customer.document_number,
                customer_business_name=customer.business_name,
                customer_contact_name=customer.contact_name,
                customer_contact_phone=customer.contact_phone,
                customer_contact_email=customer.contact_email,
                delivery_address=customer.address,
                delivery_city=customer.city,
                delivery_department=customer.department,
                delivery_neighborhood=customer.neighborhood or '',
                delivery_latitude=customer.latitude,
                delivery_longitude=customer.longitude,
                preferred_distribution_center='CEDIS-BOG',
                notes=f'Orden de prueba {i+1}',
                subtotal=Decimal('0'),  # Inicializar en 0
                tax_amount=Decimal('0'),
                discount_amount=Decimal('0'),
                total_amount=Decimal('0')
            )
            
            db.session.add(order)
            db.session.flush()  # Para obtener el ID de la orden
            
            # Agregar items a la orden (2-3 productos por orden)
            num_items = 2 if i % 2 == 0 else 3
            order_total = Decimal('0')
            
            for j in range(num_items):
                product = products[j % len(products)]
                quantity = (j + 1) * 10  # 10, 20, 30
                unit_price = Decimal(str(product['price']))
                
                item = OrderItem(
                    order_id=order.id,
                    product_sku=product['sku'],
                    product_name=product['name'],
                    quantity=quantity,
                    unit_price=unit_price,
                    discount_percentage=Decimal('0'),
                    tax_percentage=Decimal('19'),
                    distribution_center_code='CEDIS-BOG',
                    stock_confirmed=True
                )
                
                # Calcular totales
                item.calculate_totals()
                order_total += item.total
                
                db.session.add(item)
            
            # Actualizar totales de la orden
            order.subtotal = order_total
            order.tax_amount = order_total * Decimal('0.19') / Decimal('1.19')
            order.discount_amount = Decimal('0')
            order.total_amount = order_total
            
            orders_created += 1
            
            if (i + 1) % 5 == 0:
                print(f"   Creadas {i + 1} órdenes...")
        
        try:
            db.session.commit()
            print(f"✅ {orders_created} órdenes creadas exitosamente")
            print(f"\n📋 Resumen de IDs usados:")
            print(f"   Vendedores (seller_id en orders):")
            for sp in salespersons:
                print(f"      - {sp.employee_id}: {sp.get_full_name()}")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error creando órdenes: {e}")
            raise

def show_summary():
    """Muestra un resumen de los datos creados"""
    print("\n" + "="*60)
    print("📊 RESUMEN DE DATOS DE PRUEBA")
    print("="*60)
    
    with app.app_context():
        salespersons_count = Salesperson.query.count()
        customers_count = Customer.query.count()
        goals_count = SalespersonGoal.query.count()
        orders_count = Order.query.count()
        items_count = OrderItem.query.count()
        
        print(f"\n✅ Vendedores: {salespersons_count}")
        print(f"✅ Clientes: {customers_count}")
        print(f"✅ Objetivos de ventas: {goals_count}")
        print(f"✅ Órdenes: {orders_count}")
        print(f"✅ Items en órdenes: {items_count}")
        
        print("\n" + "="*60)
        print("🎯 ENDPOINTS PARA PROBAR")
        print("="*60)
        print("\n1. Health check:")
        print("   curl http://localhost:3003/reports/health")
        
        print("\n2. Reporte de ventas (mes actual):")
        current_month = datetime.utcnow().month
        current_year = datetime.utcnow().year
        print(f"   curl http://localhost:3003/reports/sales-summary?month={current_month}&year={current_year}")
        
        print("\n3. Reporte por vendedor:")
        print(f"   curl http://localhost:3003/reports/sales-by-salesperson?month={current_month}&year={current_year}")
        
        print("\n4. Reporte por producto:")
        print(f"   curl http://localhost:3003/reports/sales-by-product?month={current_month}&year={current_year}")
        
        if salespersons_count > 0:
            first_salesperson = Salesperson.query.first()
            print(f"\n5. Reporte de un vendedor específico:")
            print(f"   curl http://localhost:3003/reports/sales-summary?employee_id={first_salesperson.employee_id}")
        
        print("\n" + "="*60)

def main():
    """Función principal"""
    print("\n" + "="*60)
    print("🚀 POBLACIÓN DE DATOS DE PRUEBA PARA REPORTES")
    print("="*60)
    print("\nEste script creará datos de prueba coherentes para probar los reportes.")
    print("Los IDs estarán correctamente relacionados entre sí.")
    print("\n⚠️  ADVERTENCIA: Esto eliminará órdenes y objetivos existentes.")
    
    response = input("\n¿Continuar? (s/n): ")
    
    if response.lower() != 's':
        print("❌ Operación cancelada")
        return
    
    try:
        # Paso 1: Limpiar datos existentes
        clear_test_data()
        
        # Paso 2: Crear objetivos de ventas
        create_salesperson_goals()
        
        # Paso 3: Crear órdenes de prueba
        create_test_orders()
        
        # Paso 4: Mostrar resumen
        show_summary()
        
        print("\n" + "="*60)
        print("✅ ¡DATOS DE PRUEBA CREADOS EXITOSAMENTE!")
        print("="*60)
        print("\n💡 Ahora puedes probar el endpoint de reportes desde el frontend.")
        
    except Exception as e:
        print(f"\n❌ Error durante la creación de datos: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
