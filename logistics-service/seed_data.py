import os
import sys
from datetime import datetime, timedelta
from decimal import Decimal

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.main import create_app
from src.session import db
from src.models.distribution_center import DistributionCenter
from src.models.inventory import Inventory
from src.models.warehouse_location import WarehouseLocation
from src.models.product_batch import ProductBatch
from src.models.vehicle import Vehicle


def seed_data():
    app, socketio = create_app()
    
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
            supports_cold_chain=True,
            latitude=Decimal('4.60971'),
            longitude=Decimal('-74.08175')
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
            supports_cold_chain=True,
            latitude=Decimal('6.25184'),
            longitude=Decimal('-75.56359')
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
            supports_cold_chain=False,
            latitude=Decimal('3.43722'),
            longitude=Decimal('-76.5225')
        )
        
        db.session.add_all([dc_bogota, dc_medellin, dc_cali])
        db.session.commit()
        print(f"✅ Creados {DistributionCenter.query.count()} centros de distribución")
        
        print("📊 Creando inventarios...")
        
        # SKUs actualizados para coincidir con catalog-service
        products = [
            {'sku': 'JER-001', 'name': 'Jeringa desechable 3ml con aguja'},
            {'sku': 'JER-005', 'name': 'Jeringa desechable 5ml sin aguja'},
            {'sku': 'JER-010', 'name': 'Jeringa desechable 10ml con aguja'},
            {'sku': 'GLV-LAT-M', 'name': 'Guantes de látex talla M'},
            {'sku': 'GLV-NIL-L', 'name': 'Guantes de nitrilo talla L'},
            {'sku': 'VAC-COVID-PF', 'name': 'Vacuna COVID-19 Pfizer'},
            {'sku': 'INS-HUMAN-R', 'name': 'Insulina Humana Regular 100UI/ml'},
            {'sku': 'OX-PULSE-01', 'name': 'Oxímetro de pulso digital'},
            {'sku': 'BP-MON-AUTO', 'name': 'Tensiómetro digital automático'},
            {'sku': 'MASK-N95', 'name': 'Mascarilla N95 respirador'},
        ]
        
        inventories = []
        
        # Crear inventarios para cada producto en los diferentes centros de distribución
        for product in products:
            # Configurar cantidades especiales para productos que requieren cadena de frío
            is_cold_chain = product['sku'] in ['VAC-COVID-PF', 'INS-HUMAN-R']
            is_equipment = product['sku'] in ['OX-PULSE-01', 'BP-MON-AUTO']
            
            # Bogotá - Centro principal con cadena de frío
            inventories.append(Inventory(
                product_sku=product['sku'],
                distribution_center_id=dc_bogota.id,
                quantity_available=80 if is_cold_chain else (60 if is_equipment else 150),
                quantity_reserved=5 if is_cold_chain else 10,
                quantity_in_transit=5,
                minimum_stock_level=10 if is_cold_chain else 20,
                maximum_stock_level=200 if is_cold_chain else 500,
                reorder_point=20 if is_cold_chain else 50,
                unit_cost=Decimal('19.50') if product['sku'] == 'VAC-COVID-PF' 
                         else Decimal('24.00') if product['sku'] == 'INS-HUMAN-R'
                         else Decimal('35.00') if product['sku'] == 'OX-PULSE-01'
                         else Decimal('45.00') if product['sku'] == 'BP-MON-AUTO'
                         else Decimal('28.00') if product['sku'] == 'MASK-N95'
                         else Decimal('12.00') if product['sku'] == 'GLV-NIL-L'
                         else Decimal('8.50') if product['sku'] == 'GLV-LAT-M'
                         else Decimal('0.45') if product['sku'] == 'JER-010'
                         else Decimal('0.35') if product['sku'] == 'JER-001'
                         else Decimal('0.28'),
                last_restock_date=datetime.utcnow() - timedelta(days=5),
                last_movement_date=datetime.utcnow() - timedelta(hours=2)
            ))
            
            # Medellín - Centro secundario con cadena de frío
            inventories.append(Inventory(
                product_sku=product['sku'],
                distribution_center_id=dc_medellin.id,
                quantity_available=50 if is_cold_chain else (40 if is_equipment else 100),
                quantity_reserved=5,
                quantity_in_transit=0,
                minimum_stock_level=10 if is_cold_chain else 15,
                maximum_stock_level=150 if is_cold_chain else 300,
                reorder_point=15 if is_cold_chain else 40,
                unit_cost=Decimal('19.50') if product['sku'] == 'VAC-COVID-PF' 
                         else Decimal('24.00') if product['sku'] == 'INS-HUMAN-R'
                         else Decimal('35.00') if product['sku'] == 'OX-PULSE-01'
                         else Decimal('45.00') if product['sku'] == 'BP-MON-AUTO'
                         else Decimal('28.00') if product['sku'] == 'MASK-N95'
                         else Decimal('12.00') if product['sku'] == 'GLV-NIL-L'
                         else Decimal('8.50') if product['sku'] == 'GLV-LAT-M'
                         else Decimal('0.45') if product['sku'] == 'JER-010'
                         else Decimal('0.35') if product['sku'] == 'JER-001'
                         else Decimal('0.28'),
                last_restock_date=datetime.utcnow() - timedelta(days=3),
                last_movement_date=datetime.utcnow() - timedelta(hours=5)
            ))
            
            # Cali - Sin cadena de frío, excluir productos que la requieran
            if not is_cold_chain:
                # Crear caso especial para JER-005 (stock bajo) y MASK-N95 (out of stock)
                qty_available = 5 if product['sku'] == 'JER-005' else (0 if product['sku'] == 'MASK-N95' else (30 if is_equipment else 75))
                qty_in_transit = 20 if product['sku'] == 'JER-005' else (50 if product['sku'] == 'MASK-N95' else 10)
                qty_reserved = 0 if product['sku'] in ['JER-005', 'MASK-N95'] else 3
                min_stock = 20 if product['sku'] in ['JER-005', 'MASK-N95'] else 10
                restock_days = 30 if product['sku'] == 'JER-005' else (15 if product['sku'] == 'MASK-N95' else 7)
                last_movement_hours = 6 if product['sku'] == 'JER-005' else (48 if product['sku'] == 'MASK-N95' else 1)
                
                inventories.append(Inventory(
                    product_sku=product['sku'],
                    distribution_center_id=dc_cali.id,
                    quantity_available=qty_available,
                    quantity_reserved=qty_reserved,
                    quantity_in_transit=qty_in_transit,
                    minimum_stock_level=min_stock,
                    maximum_stock_level=200,
                    reorder_point=30,
                    unit_cost=Decimal('35.00') if product['sku'] == 'OX-PULSE-01'
                             else Decimal('45.00') if product['sku'] == 'BP-MON-AUTO'
                             else Decimal('28.00') if product['sku'] == 'MASK-N95'
                             else Decimal('12.00') if product['sku'] == 'GLV-NIL-L'
                             else Decimal('8.50') if product['sku'] == 'GLV-LAT-M'
                             else Decimal('0.45') if product['sku'] == 'JER-010'
                             else Decimal('0.35') if product['sku'] == 'JER-001'
                             else Decimal('0.28'),
                    last_restock_date=datetime.utcnow() - timedelta(days=restock_days),
                    last_movement_date=datetime.utcnow() - timedelta(hours=last_movement_hours)
                ))
        
        db.session.add_all(inventories)
        db.session.commit()
        
        print(f"✅ Creados {Inventory.query.count()} registros de inventario")
        
        print("📍 Creando ubicaciones de bodega...")
        locations = []
        
        # Ubicaciones para Bogotá (con cadena de frío)
        # Zona refrigerada
        for i in range(1, 4):
            locations.append(WarehouseLocation(
                distribution_center_id=dc_bogota.id,
                zone_type='refrigerated',
                aisle=f'A{i}',
                shelf=f'E{i}',
                level_position=f'N1-P{i}',
                temperature_min=Decimal('2.0'),
                temperature_max=Decimal('8.0'),
                current_temperature=Decimal('5.0'),
                capacity_units=100,
                is_active=True
            ))
        
        # Zona ambiente
        for i in range(1, 5):
            locations.append(WarehouseLocation(
                distribution_center_id=dc_bogota.id,
                zone_type='ambient',
                aisle=f'B{i}',
                shelf=f'E{i}',
                level_position=f'N2-P{i}',
                capacity_units=200,
                is_active=True
            ))
        
        # Ubicaciones para Medellín (con cadena de frío)
        # Zona refrigerada
        for i in range(1, 3):
            locations.append(WarehouseLocation(
                distribution_center_id=dc_medellin.id,
                zone_type='refrigerated',
                aisle=f'A{i}',
                shelf=f'E{i}',
                level_position=f'N1-P{i}',
                temperature_min=Decimal('2.0'),
                temperature_max=Decimal('8.0'),
                current_temperature=Decimal('4.5'),
                capacity_units=80,
                is_active=True
            ))
        
        # Zona ambiente
        for i in range(1, 4):
            locations.append(WarehouseLocation(
                distribution_center_id=dc_medellin.id,
                zone_type='ambient',
                aisle=f'B{i}',
                shelf=f'E{i}',
                level_position=f'N2-P{i}',
                capacity_units=150,
                is_active=True
            ))
        
        # Ubicaciones para Cali (solo ambiente, sin cadena de frío)
        for i in range(1, 5):
            locations.append(WarehouseLocation(
                distribution_center_id=dc_cali.id,
                zone_type='ambient',
                aisle=f'B{i}',
                shelf=f'E{i}',
                level_position=f'N1-P{i}',
                capacity_units=120,
                is_active=True
            ))
        
        db.session.add_all(locations)
        db.session.commit()
        
        print(f"✅ Creadas {WarehouseLocation.query.count()} ubicaciones de bodega")
        
        print("📦 Creando lotes de productos...")
        batches = []
        
        # Mapeo de productos a ubicaciones según tipo
        cold_chain_products = ['VAC-COVID-PF', 'INS-HUMAN-R']
        
        # Crear lotes con diferentes fechas de vencimiento (FEFO)
        for product in products:
            is_cold_chain = product['sku'] in cold_chain_products
            
            # Lotes para Bogotá
            if is_cold_chain:
                # Productos de cadena de frío en zonas refrigeradas
                refrigerated_locs = [l for l in locations if l.distribution_center_id == dc_bogota.id and l.zone_type == 'refrigerated']
                for idx, loc in enumerate(refrigerated_locs[:3]):
                    expiry_days = 180 - (idx * 60)  # Diferentes fechas de vencimiento para FEFO
                    batches.append(ProductBatch(
                        product_sku=product['sku'],
                        distribution_center_id=dc_bogota.id,
                        location_id=loc.id,
                        batch_number=f'BATCH-{product["sku"]}-BOG-{idx+1:02d}',
                        quantity=30 - (idx * 5),
                        expiry_date=datetime.now().date() + timedelta(days=expiry_days),
                        manufactured_date=datetime.now().date() - timedelta(days=90),
                        required_temperature_min=Decimal('2.0'),
                        required_temperature_max=Decimal('8.0'),
                        barcode=f'75012345{idx:05d}',
                        qr_code=f'QR-{product["sku"]}-{idx+1:02d}',
                        internal_code=f'INT-{product["sku"]}-{idx+1}',
                        is_available=True,
                        is_expired=False,
                        is_quarantine=False
                    ))
            else:
                # Productos ambiente
                ambient_locs = [l for l in locations if l.distribution_center_id == dc_bogota.id and l.zone_type == 'ambient']
                for idx, loc in enumerate(ambient_locs[:2]):
                    expiry_days = 360 - (idx * 90)
                    batches.append(ProductBatch(
                        product_sku=product['sku'],
                        distribution_center_id=dc_bogota.id,
                        location_id=loc.id,
                        batch_number=f'BATCH-{product["sku"]}-BOG-{idx+1:02d}',
                        quantity=50 - (idx * 10),
                        expiry_date=datetime.now().date() + timedelta(days=expiry_days),
                        manufactured_date=datetime.now().date() - timedelta(days=30),
                        barcode=f'75012345{idx:05d}',
                        qr_code=f'QR-{product["sku"]}-{idx+1:02d}',
                        internal_code=f'INT-{product["sku"]}-{idx+1}',
                        is_available=True,
                        is_expired=False,
                        is_quarantine=False
                    ))
            
            # Lotes para Medellín
            if is_cold_chain:
                refrigerated_locs = [l for l in locations if l.distribution_center_id == dc_medellin.id and l.zone_type == 'refrigerated']
                for idx, loc in enumerate(refrigerated_locs[:2]):
                    expiry_days = 150 - (idx * 45)
                    batches.append(ProductBatch(
                        product_sku=product['sku'],
                        distribution_center_id=dc_medellin.id,
                        location_id=loc.id,
                        batch_number=f'BATCH-{product["sku"]}-MED-{idx+1:02d}',
                        quantity=25 - (idx * 5),
                        expiry_date=datetime.now().date() + timedelta(days=expiry_days),
                        manufactured_date=datetime.now().date() - timedelta(days=60),
                        required_temperature_min=Decimal('2.0'),
                        required_temperature_max=Decimal('8.0'),
                        barcode=f'75098765{idx:05d}',
                        qr_code=f'QR-{product["sku"]}-MED-{idx+1:02d}',
                        internal_code=f'INT-MED-{product["sku"]}-{idx+1}',
                        is_available=True,
                        is_expired=False,
                        is_quarantine=False
                    ))
            else:
                ambient_locs = [l for l in locations if l.distribution_center_id == dc_medellin.id and l.zone_type == 'ambient']
                for idx, loc in enumerate(ambient_locs[:2]):
                    expiry_days = 270 - (idx * 60)
                    batches.append(ProductBatch(
                        product_sku=product['sku'],
                        distribution_center_id=dc_medellin.id,
                        location_id=loc.id,
                        batch_number=f'BATCH-{product["sku"]}-MED-{idx+1:02d}',
                        quantity=40 - (idx * 10),
                        expiry_date=datetime.now().date() + timedelta(days=expiry_days),
                        manufactured_date=datetime.now().date() - timedelta(days=20),
                        barcode=f'75098765{idx:05d}',
                        qr_code=f'QR-{product["sku"]}-MED-{idx+1:02d}',
                        internal_code=f'INT-MED-{product["sku"]}-{idx+1}',
                        is_available=True,
                        is_expired=False,
                        is_quarantine=False
                    ))
            
            # Lotes para Cali (solo productos sin cadena de frío)
            if not is_cold_chain:
                ambient_locs = [l for l in locations if l.distribution_center_id == dc_cali.id]
                for idx, loc in enumerate(ambient_locs[:2]):
                    # Crear caso especial: un lote cerca del vencimiento
                    if product['sku'] == 'JER-005' and idx == 0:
                        expiry_days = 25  # Cerca del vencimiento
                        quantity = 5
                    else:
                        expiry_days = 240 - (idx * 60)
                        quantity = 30 - (idx * 10)
                    
                    batches.append(ProductBatch(
                        product_sku=product['sku'],
                        distribution_center_id=dc_cali.id,
                        location_id=loc.id,
                        batch_number=f'BATCH-{product["sku"]}-CAL-{idx+1:02d}',
                        quantity=quantity,
                        expiry_date=datetime.now().date() + timedelta(days=expiry_days),
                        manufactured_date=datetime.now().date() - timedelta(days=15),
                        barcode=f'75054321{idx:05d}',
                        qr_code=f'QR-{product["sku"]}-CAL-{idx+1:02d}',
                        internal_code=f'INT-CAL-{product["sku"]}-{idx+1}',
                        is_available=True,
                        is_expired=False,
                        is_quarantine=False
                    ))
        
        db.session.add_all(batches)
        db.session.commit()
        
        print(f"✅ Creados {ProductBatch.query.count()} lotes de productos")
        
        print("\n📊 Resumen de datos:")
        print(f"  Centros de distribución: {DistributionCenter.query.count()}")
        print(f"  Registros de inventario: {Inventory.query.count()}")
        print(f"  Ubicaciones de bodega: {WarehouseLocation.query.count()}")
        print(f"  Lotes de productos: {ProductBatch.query.count()}")
        print(f"  Productos únicos: {len(set([i.product_sku for i in Inventory.query.all()]))}")
        
        # Mostrar algunos ejemplos de lotes por vencer (FEFO)
        near_expiry_batches = ProductBatch.query.filter(
            ProductBatch.expiry_date <= datetime.now().date() + timedelta(days=60)
        ).order_by(ProductBatch.expiry_date).limit(5).all()
        
        if near_expiry_batches:
            print("\n⚠️  Lotes próximos a vencer (FEFO - primeros 5):")
            for batch in near_expiry_batches:
                days_left = (batch.expiry_date - datetime.now().date()).days
                print(f"  - {batch.product_sku} | Lote: {batch.batch_number} | Vence en {days_left} días | Cantidad: {batch.quantity}")
        
        # ============================================================================
        # VEHÍCULOS (HU-077 - Route Optimization)
        # ============================================================================
        print("\n🚚 Creando vehículos para la flota...")
        
        vehicles = [
            # Vehículos con refrigeración - Bogotá
            Vehicle(
                plate='ABC-123',
                vehicle_type='refrigerated_truck',
                brand='Chevrolet',
                model='NPR',
                year=2022,
                capacity_kg=Decimal('3000.00'),
                capacity_m3=Decimal('18.00'),
                has_refrigeration=True,
                temperature_min=Decimal('-20.00'),
                temperature_max=Decimal('8.00'),
                max_stops_per_route=12,
                avg_speed_kmh=Decimal('35.00'),
                cost_per_km=Decimal('3.50'),
                home_distribution_center_id=dc_bogota.id,
                driver_name='Juan Carlos Méndez',
                driver_phone='+57 300 123 4567',
                driver_license='C1234567',
                is_available=True,
                is_active=True,
                current_location_lat=Decimal('4.60971'),
                current_location_lng=Decimal('-74.08175'),
                notes='Vehículo equipado con sistema de refrigeración -20°C a 8°C. Ideal para vacunas e insulina.'
            ),
            Vehicle(
                plate='DEF-456',
                vehicle_type='refrigerated_truck',
                brand='Hino',
                model='Serie 300',
                year=2023,
                capacity_kg=Decimal('2500.00'),
                capacity_m3=Decimal('15.00'),
                has_refrigeration=True,
                temperature_min=Decimal('2.00'),
                temperature_max=Decimal('8.00'),
                max_stops_per_route=10,
                avg_speed_kmh=Decimal('38.00'),
                cost_per_km=Decimal('3.20'),
                home_distribution_center_id=dc_bogota.id,
                driver_name='María Fernanda López',
                driver_phone='+57 301 234 5678',
                driver_license='C2345678',
                is_available=True,
                is_active=True,
                current_location_lat=Decimal('4.60971'),
                current_location_lng=Decimal('-74.08175'),
                notes='Refrigeración 2-8°C. Perfecto para medicamentos biológicos.'
            ),
            
            # Vehículos estándar - Bogotá
            Vehicle(
                plate='GHI-789',
                vehicle_type='van',
                brand='Ford',
                model='Transit',
                year=2021,
                capacity_kg=Decimal('1500.00'),
                capacity_m3=Decimal('10.00'),
                has_refrigeration=False,
                max_stops_per_route=15,
                avg_speed_kmh=Decimal('42.00'),
                cost_per_km=Decimal('2.50'),
                home_distribution_center_id=dc_bogota.id,
                driver_name='Pedro Sánchez',
                driver_phone='+57 302 345 6789',
                driver_license='C3456789',
                is_available=True,
                is_active=True,
                current_location_lat=Decimal('4.60971'),
                current_location_lng=Decimal('-74.08175'),
                notes='Van estándar para productos que no requieren cadena de frío.'
            ),
            Vehicle(
                plate='JKL-012',
                vehicle_type='truck',
                brand='Chevrolet',
                model='NKR',
                year=2020,
                capacity_kg=Decimal('2000.00'),
                capacity_m3=Decimal('14.00'),
                has_refrigeration=False,
                max_stops_per_route=12,
                avg_speed_kmh=Decimal('40.00'),
                cost_per_km=Decimal('2.80'),
                home_distribution_center_id=dc_bogota.id,
                driver_name='Luis Alberto Ramírez',
                driver_phone='+57 303 456 7890',
                driver_license='C4567890',
                is_available=True,
                is_active=True,
                current_location_lat=Decimal('4.60971'),
                current_location_lng=Decimal('-74.08175'),
                notes='Camión para cargas voluminosas sin refrigeración.'
            ),
            
            # Vehículos - Medellín
            Vehicle(
                plate='MNO-345',
                vehicle_type='refrigerated_truck',
                brand='Isuzu',
                model='NLR',
                year=2022,
                capacity_kg=Decimal('2800.00'),
                capacity_m3=Decimal('16.00'),
                has_refrigeration=True,
                temperature_min=Decimal('-20.00'),
                temperature_max=Decimal('8.00'),
                max_stops_per_route=10,
                avg_speed_kmh=Decimal('36.00'),
                cost_per_km=Decimal('3.30'),
                home_distribution_center_id=dc_medellin.id,
                driver_name='Carlos Andrés Gómez',
                driver_phone='+57 304 567 8901',
                driver_license='C5678901',
                is_available=True,
                is_active=True,
                current_location_lat=Decimal('6.25184'),
                current_location_lng=Decimal('-75.56359'),
                notes='Refrigerado para Medellín y área metropolitana.'
            ),
            Vehicle(
                plate='PQR-678',
                vehicle_type='van',
                brand='Renault',
                model='Master',
                year=2023,
                capacity_kg=Decimal('1400.00'),
                capacity_m3=Decimal('9.00'),
                has_refrigeration=False,
                max_stops_per_route=14,
                avg_speed_kmh=Decimal('43.00'),
                cost_per_km=Decimal('2.40'),
                home_distribution_center_id=dc_medellin.id,
                driver_name='Ana María Pérez',
                driver_phone='+57 305 678 9012',
                driver_license='C6789012',
                is_available=True,
                is_active=True,
                current_location_lat=Decimal('6.25184'),
                current_location_lng=Decimal('-75.56359'),
                notes='Van ágil para entregas urbanas en Medellín.'
            ),
            
            # Vehículos - Cali
            Vehicle(
                plate='STU-901',
                vehicle_type='van',
                brand='Mercedes-Benz',
                model='Sprinter',
                year=2022,
                capacity_kg=Decimal('1600.00'),
                capacity_m3=Decimal('11.00'),
                has_refrigeration=False,
                max_stops_per_route=13,
                avg_speed_kmh=Decimal('41.00'),
                cost_per_km=Decimal('2.60'),
                home_distribution_center_id=dc_cali.id,
                driver_name='Roberto Castro',
                driver_phone='+57 306 789 0123',
                driver_license='C7890123',
                is_available=True,
                is_active=True,
                current_location_lat=Decimal('3.43722'),
                current_location_lng=Decimal('-76.5225'),
                notes='Sprinter para Cali, sin refrigeración.'
            ),
            Vehicle(
                plate='VWX-234',
                vehicle_type='truck',
                brand='Hino',
                model='Serie 500',
                year=2021,
                capacity_kg=Decimal('3500.00'),
                capacity_m3=Decimal('20.00'),
                has_refrigeration=False,
                max_stops_per_route=10,
                avg_speed_kmh=Decimal('38.00'),
                cost_per_km=Decimal('3.00'),
                home_distribution_center_id=dc_cali.id,
                driver_name='Sandra Milena Torres',
                driver_phone='+57 307 890 1234',
                driver_license='C8901234',
                is_available=True,
                is_active=True,
                current_location_lat=Decimal('3.43722'),
                current_location_lng=Decimal('-76.5225'),
                notes='Camión grande para Cali, capacidad extendida.'
            ),
            
            # Vehículo en mantenimiento (no disponible)
            Vehicle(
                plate='YZA-567',
                vehicle_type='refrigerated_truck',
                brand='Chevrolet',
                model='NPR',
                year=2019,
                capacity_kg=Decimal('2700.00'),
                capacity_m3=Decimal('16.00'),
                has_refrigeration=True,
                temperature_min=Decimal('-15.00'),
                temperature_max=Decimal('8.00'),
                max_stops_per_route=11,
                avg_speed_kmh=Decimal('35.00'),
                cost_per_km=Decimal('3.40'),
                home_distribution_center_id=dc_bogota.id,
                driver_name='Miguel Ángel Vargas',
                driver_phone='+57 308 901 2345',
                driver_license='C9012345',
                is_available=False,  # En mantenimiento
                is_active=True,
                current_location_lat=Decimal('4.60971'),
                current_location_lng=Decimal('-74.08175'),
                last_maintenance_date=datetime.now().date() - timedelta(days=5),
                next_maintenance_date=datetime.now().date() + timedelta(days=85),
                notes='En mantenimiento preventivo. Refrigerado. Estará disponible próximamente.'
            ),
        ]
        
        db.session.add_all(vehicles)
        db.session.commit()
        print(f"✅ Creados {Vehicle.query.count()} vehículos")
        
        # Resumen de vehículos por tipo
        refrigerated_count = Vehicle.query.filter_by(has_refrigeration=True).count()
        available_count = Vehicle.query.filter_by(is_available=True).count()
        print(f"   - Vehículos refrigerados: {refrigerated_count}")
        print(f"   - Vehículos disponibles: {available_count}")
        print(f"   - Vehículos en mantenimiento: {Vehicle.query.filter_by(is_available=False).count()}")
        
        print("\n✅ Seed completado exitosamente!")


if __name__ == '__main__':
    seed_data()
