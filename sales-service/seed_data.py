"""
Seed data script for sales-service development database.
Creates sample customers for testing.
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.main import create_app
from src.session import db
from src.models.customer import Customer


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
        
        print("\n📊 Resumen de datos:")
        print(f"  Clientes: {len(customers)}")
        print("\n✅ Seed completado exitosamente!")


if __name__ == '__main__':
    main()
