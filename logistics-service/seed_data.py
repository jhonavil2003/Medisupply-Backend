import os
import sys
from datetime import datetime, timedelta
from decimal import Decimal

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.main import create_app
from src.session import db
from src.models.distribution_center import DistributionCenter
from src.models.inventory import Inventory


def seed_data():
    app = create_app()
    
    with app.app_context():
        print("🌱 Iniciando seed de datos...")
        
        print("�️  Clearing existing data...")
        db.drop_all()
        db.create_all()
        
        print("�📦 Creando centros de distribución...")
        dc_bogota = DistributionCenter(
            code='DC-BOG-001',
            name='Centro de Distribución Bogotá',
            address='Calle 100 # 15-20',
            city='Bogotá',
            state='Cundinamarca',
            country='Colombia',
            postal_code='110111',
            phone='+57 1 234 5678',
            email='bogota@medisupply.com',
            manager_name='Carlos Rodríguez',
            capacity_m3=Decimal('5000.00'),
            is_active=True,
            supports_cold_chain=True
        )
        
        dc_medellin = DistributionCenter(
            code='DC-MED-001',
            name='Centro de Distribución Medellín',
            address='Carrera 50 # 30-15',
            city='Medellín',
            state='Antioquia',
            country='Colombia',
            postal_code='050001',
            phone='+57 4 567 8901',
            email='medellin@medisupply.com',
            manager_name='Ana María López',
            capacity_m3=Decimal('3000.00'),
            is_active=True,
            supports_cold_chain=True
        )
        
        dc_cali = DistributionCenter(
            code='DC-CAL-001',
            name='Centro de Distribución Cali',
            address='Avenida 6N # 25-40',
            city='Cali',
            state='Valle del Cauca',
            country='Colombia',
            postal_code='760001',
            phone='+57 2 345 6789',
            email='cali@medisupply.com',
            manager_name='Jorge Martínez',
            capacity_m3=Decimal('2500.00'),
            is_active=True,
            supports_cold_chain=False
        )
        
        db.session.add_all([dc_bogota, dc_medellin, dc_cali])
        db.session.commit()
        print(f"✅ Creados {DistributionCenter.query.count()} centros de distribución")
        
        print("📊 Creando inventarios...")
        
        products = [
            {'sku': 'JER-001', 'name': 'Jeringa desechable 3ml'},
            {'sku': 'GUANTE-001', 'name': 'Guantes de látex'},
            {'sku': 'VAC-001', 'name': 'Vacuna COVID-19'},
            {'sku': 'MASCA-001', 'name': 'Mascarilla N95'},
            {'sku': 'TERM-001', 'name': 'Termómetro digital'},
            {'sku': 'GASA-001', 'name': 'Gasa estéril 10x10'},
            {'sku': 'ALCO-001', 'name': 'Alcohol antiséptico 500ml'},
            {'sku': 'BAND-001', 'name': 'Vendaje elástico 5cm'},
        ]
        
        inventories = []
        
        for product in products:
            inventories.append(Inventory(
                product_sku=product['sku'],
                distribution_center_id=dc_bogota.id,
                quantity_available=150 if product['sku'] != 'VAC-001' else 80,
                quantity_reserved=10 if product['sku'] != 'GASA-001' else 0,
                quantity_in_transit=5,
                minimum_stock_level=20,
                maximum_stock_level=500,
                reorder_point=50,
                unit_cost=Decimal('2.50'),
                last_restock_date=datetime.utcnow() - timedelta(days=5),
                last_movement_date=datetime.utcnow() - timedelta(hours=2)
            ))
            
            inventories.append(Inventory(
                product_sku=product['sku'],
                distribution_center_id=dc_medellin.id,
                quantity_available=100 if product['sku'] != 'TERM-001' else 50,
                quantity_reserved=5,
                quantity_in_transit=0,
                minimum_stock_level=15,
                maximum_stock_level=300,
                reorder_point=40,
                unit_cost=Decimal('2.30'),
                last_restock_date=datetime.utcnow() - timedelta(days=3),
                last_movement_date=datetime.utcnow() - timedelta(hours=5)
            ))
            
            if product['sku'] not in ['VAC-001', 'TERM-001']:
                inventories.append(Inventory(
                    product_sku=product['sku'],
                    distribution_center_id=dc_cali.id,
                    quantity_available=75,
                    quantity_reserved=3,
                    quantity_in_transit=10,
                    minimum_stock_level=10,
                    maximum_stock_level=200,
                    reorder_point=30,
                    unit_cost=Decimal('2.40'),
                    last_restock_date=datetime.utcnow() - timedelta(days=7),
                    last_movement_date=datetime.utcnow() - timedelta(hours=1)
                ))
        
        inventories.append(Inventory(
            product_sku='LOW-STOCK-001',
            distribution_center_id=dc_bogota.id,
            quantity_available=5,
            quantity_reserved=0,
            quantity_in_transit=0,
            minimum_stock_level=20,
            maximum_stock_level=100,
            reorder_point=20,
            unit_cost=Decimal('15.00'),
            last_restock_date=datetime.utcnow() - timedelta(days=30),
            last_movement_date=datetime.utcnow() - timedelta(hours=6)
        ))
        
        inventories.append(Inventory(
            product_sku='OUT-OF-STOCK-001',
            distribution_center_id=dc_medellin.id,
            quantity_available=0,
            quantity_reserved=0,
            quantity_in_transit=50,
            minimum_stock_level=30,
            maximum_stock_level=150,
            reorder_point=50,
            unit_cost=Decimal('8.00'),
            last_restock_date=datetime.utcnow() - timedelta(days=15),
            last_movement_date=datetime.utcnow() - timedelta(days=2)
        ))
        
        db.session.add_all(inventories)
        db.session.commit()
        
        print(f"✅ Creados {Inventory.query.count()} registros de inventario")
        
        print("\n📊 Resumen de datos:")
        print(f"  Centros de distribución: {DistributionCenter.query.count()}")
        print(f"  Registros de inventario: {Inventory.query.count()}")
        print(f"  Productos únicos: {len(set([i.product_sku for i in Inventory.query.all()]))}")
        
        print("\n✅ Seed completado exitosamente!")


if __name__ == '__main__':
    seed_data()
