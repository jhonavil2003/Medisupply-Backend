"""
Script para crear las tablas de visit_routes y visit_route_stops en la base de datos.

Este script debe ejecutarse una sola vez para crear las tablas necesarias
para la funcionalidad de rutas de visitas a clientes.
"""

import os
import sys
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Agregar el directorio src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from flask import Flask
from src.session import db
from src.models.visit_route import VisitRoute
from src.models.visit_route_stop import VisitRouteStop

def create_tables():
    """Crea las tablas de visit_routes y visit_route_stops."""
    
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
        'DATABASE_URL',
        'postgresql://logisticsuser:logistics_secure_password_2024@localhost:5433/logistics_db'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    with app.app_context():
        print("🔧 Creando tablas de rutas de visitas...")
        print(f"📊 Base de datos: {app.config['SQLALCHEMY_DATABASE_URI']}")
        
        # Crear solo las tablas específicas
        VisitRoute.__table__.create(db.engine, checkfirst=True)
        print("✅ Tabla 'visit_routes' creada")
        
        VisitRouteStop.__table__.create(db.engine, checkfirst=True)
        print("✅ Tabla 'visit_route_stops' creada")
        
        print("\n✅ Todas las tablas de rutas de visitas han sido creadas exitosamente!")
        print("\n📝 Estructura de las tablas:")
        print("\nvisit_routes:")
        print("  - id (PK)")
        print("  - route_code (UNIQUE)")
        print("  - salesperson_id, salesperson_name, salesperson_employee_id")
        print("  - planned_date, status")
        print("  - total_stops, total_distance_km, estimated_duration_minutes")
        print("  - optimization_strategy, optimization_score")
        print("  - start/end location data")
        print("  - work hours")
        print("  - map_url")
        print("  - timestamps (created_at, updated_at)")
        
        print("\nvisit_route_stops:")
        print("  - id (PK)")
        print("  - visit_route_id (FK)")
        print("  - sequence_order")
        print("  - customer_id, customer_name, customer_code")
        print("  - location data (address, city, latitude, longitude)")
        print("  - contact data (name, phone)")
        print("  - estimated times (arrival, departure, service)")
        print("  - actual times (arrival, departure)")
        print("  - distance_from_previous_km, travel_time_from_previous_minutes")
        print("  - is_completed, is_skipped, completed_at, skipped_at")
        print("  - notes, skip_reason")
        print("  - timestamps (created_at, updated_at)")

if __name__ == '__main__':
    try:
        create_tables()
    except Exception as e:
        print(f"\n❌ Error creando tablas: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
