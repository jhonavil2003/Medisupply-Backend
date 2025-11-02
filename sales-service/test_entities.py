#!/usr/bin/env python3
"""
Script de prueba para verificar que las entidades se pueden crear correctamente
Uso: python test_entities.py
"""

import sys
import os
from datetime import date, time
from decimal import Decimal

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    from src.entities.visit_status import VisitStatus
    from src.entities.salesperson import Salesperson
    from src.entities.visit import Visit
    from src.entities.visit_file import VisitFile
    
    print("✅ Importación de entidades exitosa")
    
    # Test VisitStatus
    print("\n🔍 Testing VisitStatus...")
    status = VisitStatus.PROGRAMADA
    print(f"   Status created: {status} (value: {status.value})")
    
    # Test Salesperson
    print("\n🔍 Testing Salesperson...")
    salesperson = Salesperson(
        employee_id="SELLER-001",
        first_name="Juan",
        last_name="Pérez",
        email="juan.perez@medisupply.com",
        phone="+57 300 1234567",
        territory="Bogotá Norte",
        hire_date=date(2023, 1, 15)
    )
    print(f"   Salesperson created: {salesperson}")
    print(f"   Full name: {salesperson.get_full_name()}")
    print(f"   Employee ID: {salesperson.get_employee_id()}")
    print(f"   Territory: {salesperson.get_territory_display()}")
    
    # Test Visit
    print("\n🔍 Testing Visit...")
    visit = Visit(
        customer_id=1,
        salesperson_id=1,
        visit_date=date(2025, 10, 30),
        visit_time=time(14, 30),
        contacted_persons="Dr. María González",
        clinical_findings="Revisión de inventario necesaria",
        additional_notes="Cliente interesado en nuevos productos",
        address="Calle 10 #5-25, Bogotá",
        latitude=Decimal("4.60971"),
        longitude=Decimal("-74.08175"),
        status=VisitStatus.PROGRAMADA
    )
    print(f"   Visit created: {visit}")
    print(f"   Visit date: {visit.get_visit_date()}")
    print(f"   Visit time: {visit.get_visit_time()}")
    print(f"   Status: {visit.get_status()}")
    print(f"   Is scheduled: {visit.is_scheduled()}")
    
    # Test VisitFile
    print("\n🔍 Testing VisitFile...")
    visit_file = VisitFile(
        visit_id=1,
        file_name="inventory_report.pdf",
        file_path="/uploads/visits/1/inventory_report.pdf",
        file_size=1024000,  # 1MB
        mime_type="application/pdf"
    )
    print(f"   VisitFile created: {visit_file}")
    print(f"   File name: {visit_file.get_file_name()}")
    print(f"   File size: {visit_file.get_file_size_formatted()}")
    print(f"   Is document: {visit_file.is_document()}")
    
    # Test serialization
    print("\n🔍 Testing serialization...")
    salesperson_dict = salesperson.to_dict()
    visit_dict = visit.to_dict()
    visit_file_dict = visit_file.to_dict()
    
    print(f"   Salesperson dict keys: {list(salesperson_dict.keys())}")
    print(f"   Visit dict keys: {list(visit_dict.keys())}")
    print(f"   VisitFile dict keys: {list(visit_file_dict.keys())}")
    
    print("\n✅ Todas las pruebas de entidades pasaron exitosamente!")
    print("\n📋 Resumen de entidades creadas:")
    print(f"   - VisitStatus: Enum con 3 valores (PROGRAMADA, COMPLETADA, ELIMINADA)")
    print(f"   - Salesperson: {salesperson.get_full_name()} - {salesperson.get_territory()}")
    print(f"   - Visit: {visit.get_visit_date()} a las {visit.get_visit_time()}")
    print(f"   - VisitFile: {visit_file.get_file_name()} ({visit_file.get_file_size_formatted()})")
    
except ImportError as e:
    print(f"❌ Error de importación: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error durante las pruebas: {e}")
    sys.exit(1)