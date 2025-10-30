#!/usr/bin/env python3
"""
Script para insertar datos de prueba en el servicio de visitas
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date, time, datetime, timedelta
from decimal import Decimal
from src.main import create_app
from src.session import db
from src.entities.salesperson import Salesperson
from src.entities.visit import Visit
from src.entities.visit_status import VisitStatus


def create_seed_data():
    """Crear datos de prueba"""
    
    print("🌱 Insertando datos de prueba para visits-service...")
    
    # Crear vendedores adicionales si no existen
    salespersons_data = [
        {
            'employee_id': 'SELLER-006',
            'first_name': 'Laura',
            'last_name': 'Ramírez',
            'email': 'laura.ramirez@medisupply.com',
            'phone': '+57 300 6789012',
            'territory': 'Bucaramanga',
            'hire_date': date(2024, 02, 15),
            'is_active': True
        },
        {
            'employee_id': 'SELLER-007',
            'first_name': 'Roberto',
            'last_name': 'Silva',
            'email': 'roberto.silva@medisupply.com',
            'phone': '+57 300 7890123',
            'territory': 'Pereira',
            'hire_date': date(2024, 03, 20),
            'is_active': True
        }
    ]
    
    # Insertar vendedores
    for sp_data in salespersons_data:
        existing = db.session.query(Salesperson).filter_by(employee_id=sp_data['employee_id']).first()
        if not existing:
            salesperson = Salesperson(**sp_data)
            db.session.add(salesperson)
            print(f"   ✅ Vendedor creado: {sp_data['first_name']} {sp_data['last_name']}")
    
    db.session.commit()
    
    # Obtener vendedores para crear visitas
    salespersons = db.session.query(Salesperson).all()
    
    # Crear visitas de ejemplo
    visits_data = [
        {
            'customer_id': 1,  # Asumiendo cliente del sales-service
            'salesperson_id': salespersons[0].id if salespersons else 1,
            'visit_date': date.today() + timedelta(days=1),
            'visit_time': time(9, 30),
            'contacted_persons': 'Dr. Ana García - Jefe de Compras',
            'clinical_findings': 'Necesidad de reposición de material quirúrgico',
            'additional_notes': 'Cliente interesado en nuevos productos ortopédicos',
            'address': 'Calle 72 #10-25, Bogotá',
            'latitude': Decimal('4.65389'),
            'longitude': Decimal('-74.08333'),
            'status': VisitStatus.SCHEDULED
        },
        {
            'customer_id': 2,
            'salesperson_id': salespersons[1].id if len(salespersons) > 1 else 1,
            'visit_date': date.today() + timedelta(days=2),
            'visit_time': time(14, 0),
            'contacted_persons': 'Dra. Carmen López - Directora Médica',
            'clinical_findings': 'Revisión de inventario actual',
            'additional_notes': 'Posible pedido de equipos de diagnóstico',
            'address': 'Carrera 15 #85-12, Bogotá',
            'latitude': Decimal('4.67389'),
            'longitude': Decimal('-74.06333'),
            'status': VisitStatus.SCHEDULED
        },
        {
            'customer_id': 1,
            'salesperson_id': salespersons[0].id if salespersons else 1,
            'visit_date': date.today() - timedelta(days=7),
            'visit_time': time(11, 0),
            'contacted_persons': 'Dr. Carlos Mendoza - Coordinador de Compras',
            'clinical_findings': 'Satisfacción con productos entregados anteriormente',
            'additional_notes': 'Visita de seguimiento exitosa',
            'address': 'Calle 72 #10-25, Bogotá',
            'latitude': Decimal('4.65389'),
            'longitude': Decimal('-74.08333'),
            'status': VisitStatus.COMPLETED
        },
        {
            'customer_id': 3,
            'salesperson_id': salespersons[2].id if len(salespersons) > 2 else 1,
            'visit_date': date.today() + timedelta(days=5),
            'visit_time': time(10, 30),
            'contacted_persons': 'Dr. María Rodríguez - Administradora',
            'clinical_findings': 'Evaluación de necesidades para nuevo departamento',
            'additional_notes': 'Cliente potencial para grandes volúmenes',
            'address': 'Avenida 19 #120-30, Medellín',
            'latitude': Decimal('6.25389'),
            'longitude': Decimal('-75.56333'),
            'status': VisitStatus.SCHEDULED
        },
        {
            'customer_id': 2,
            'salesperson_id': salespersons[1].id if len(salespersons) > 1 else 1,
            'visit_date': date.today() - timedelta(days=3),
            'visit_time': time(16, 0),
            'contacted_persons': 'Dr. Luis Herrera - Jefe de Urgencias',
            'clinical_findings': 'Urgente necesidad de material de emergencia',
            'additional_notes': 'Programar entrega prioritaria',
            'address': 'Carrera 15 #85-12, Bogotá',
            'latitude': Decimal('4.67389'),
            'longitude': Decimal('-74.06333'),
            'status': VisitStatus.COMPLETED
        }
    ]
    
    # Insertar visitas
    for visit_data in visits_data:
        visit = Visit(**visit_data)
        db.session.add(visit)
        print(f"   ✅ Visita creada: Cliente {visit_data['customer_id']} - {visit_data['visit_date']}")
    
    db.session.commit()
    
    print("🌱 ¡Datos de prueba insertados exitosamente!")
    print(f"   📊 Vendedores totales: {db.session.query(Salesperson).count()}")
    print(f"   📅 Visitas totales: {db.session.query(Visit).count()}")


if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        create_seed_data()