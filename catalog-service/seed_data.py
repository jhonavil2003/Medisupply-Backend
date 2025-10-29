import os
import sys
from datetime import datetime, date, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.main import create_app
from src.session import db
from src.models.supplier import Supplier
from src.models.product import Product
from src.models.certification import Certification
from src.models.regulatory_condition import RegulatoryCondition

# Import shared seed data
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from shared_seed_data import SUPPLIERS_DATA, PRODUCTS_DATA

def seed_data():
    app = create_app()
    
    with app.app_context():
        print("🗑️  Clearing existing data...")
        db.drop_all()
        db.create_all()
        
        print("👥 Creating suppliers...")
        suppliers = []
        for supplier_data in SUPPLIERS_DATA:
            supplier = Supplier(
                name=supplier_data['name'],
                legal_name=supplier_data['legal_name'],
                tax_id=supplier_data['tax_id'],
                email=supplier_data['email'],
                phone=supplier_data['phone'],
                country=supplier_data['country'],
                city=supplier_data['city'],
                is_certified=supplier_data['is_certified'],
                certification_date=supplier_data['certification_date'],
                certification_expiry=supplier_data['certification_expiry'],
                is_active=supplier_data['is_active']
            )
            suppliers.append(supplier)
        
        db.session.add_all(suppliers)
        db.session.commit()
        print(f"✅ Created {len(suppliers)} suppliers")
        
        print("📦 Creating products...")
        products = []
        for product_data in PRODUCTS_DATA:
            product_dict = {
                'sku': product_data['sku'],
                'name': product_data['name'],
                'description': product_data['description'],
                'category': product_data['category'],
                'subcategory': product_data['subcategory'],
                'unit_price': product_data['unit_price'],
                'currency': product_data['currency'],
                'unit_of_measure': product_data['unit_of_measure'],
                'supplier_id': suppliers[product_data['supplier_id'] - 1].id,
                'requires_cold_chain': product_data['requires_cold_chain'],
                'sanitary_registration': product_data['sanitary_registration'],
                'requires_prescription': product_data['requires_prescription'],
                'regulatory_class': product_data['regulatory_class'],
                'weight_kg': product_data['weight_kg'],
                'manufacturer': product_data['manufacturer'],
                'country_of_origin': product_data['country_of_origin'],
                'barcode': product_data['barcode'],
                'is_active': product_data['is_active']
            }
            
            # Add optional fields if present
            if 'storage_temperature_min' in product_data:
                product_dict['storage_temperature_min'] = product_data['storage_temperature_min']
            if 'storage_temperature_max' in product_data:
                product_dict['storage_temperature_max'] = product_data['storage_temperature_max']
            if 'length_cm' in product_data:
                product_dict['length_cm'] = product_data['length_cm']
            if 'width_cm' in product_data:
                product_dict['width_cm'] = product_data['width_cm']
            if 'height_cm' in product_data:
                product_dict['height_cm'] = product_data['height_cm']
            
            product = Product(**product_dict)
            products.append(product)
        
        db.session.add_all(products)
        db.session.commit()
        print(f"✅ Created {len(products)} products")
        
        # Create certifications
        print("📜 Creating certifications...")
        certifications = [
            # Certifications for vaccine
            Certification(
                product_id=next((p.id for p in products if p.sku == 'VAC-COVID-PF'), None),
                certification_type="FDA",
                certification_number="BLA-125742",
                issuing_authority="U.S. Food and Drug Administration",
                country="USA",
                issue_date=date(2020, 12, 11),
                expiry_date=date(2025, 12, 11),
                is_valid=True
            ),
            Certification(
                product_id=next((p.id for p in products if p.sku == 'VAC-COVID-PF'), None),
                certification_type="INVIMA",
                certification_number="INVIMA-2021-0012345",
                issuing_authority="Instituto Nacional de Vigilancia de Medicamentos y Alimentos",
                country="Colombia",
                issue_date=date(2021, 2, 15),
                expiry_date=date(2026, 2, 15),
                is_valid=True
            ),
            # Certifications for insulin
            Certification(
                product_id=next((p.id for p in products if p.sku == 'INS-HUMAN-R'), None),
                certification_type="DIGEMID",
                certification_number="DIGEMID-2020-5678",
                issuing_authority="Dirección General de Medicamentos, Insumos y Drogas",
                country="Peru",
                issue_date=date(2020, 6, 1),
                expiry_date=date(2025, 6, 1),
                is_valid=True
            ),
        ]
        
        db.session.add_all(certifications)
        db.session.commit()
        print(f"✅ Created {len(certifications)} certifications")
        
        # Create regulatory conditions
        print("⚖️  Creating regulatory conditions...")
        regulatory_conditions = [
            # Regulatory conditions for vaccine in different countries
            RegulatoryCondition(
                product_id=next((p.id for p in products if p.sku == 'VAC-COVID-PF'), None),
                country="Colombia",
                regulatory_body="INVIMA",
                import_restrictions="Requiere autorización especial de importación",
                special_handling_requirements="Mantener en ultra congelación (-80°C a -60°C) hasta su uso",
                distribution_restrictions="Solo puede ser distribuido por centros autorizados",
                required_documentation="Certificado de origen, Certificado de análisis, Cadena de frío",
                is_approved_for_sale=True,
                approval_date=date(2021, 2, 15)
            ),
            RegulatoryCondition(
                product_id=next((p.id for p in products if p.sku == 'VAC-COVID-PF'), None),
                country="Peru",
                regulatory_body="DIGEMID",
                import_restrictions="Requiere registro sanitario previo",
                special_handling_requirements="Mantener cadena de frío extrema",
                distribution_restrictions="Distribución controlada por MINSA",
                required_documentation="Certificado FDA, Certificado de origen",
                is_approved_for_sale=True,
                approval_date=date(2021, 3, 1)
            ),
            # Regulatory conditions for insulin
            RegulatoryCondition(
                product_id=next((p.id for p in products if p.sku == 'INS-HUMAN-R'), None),
                country="Colombia",
                regulatory_body="INVIMA",
                import_restrictions="Producto controlado - Requiere receta médica",
                special_handling_requirements="Mantener refrigerado (2-8°C)",
                distribution_restrictions="Venta solo en farmacias autorizadas",
                required_documentation="Registro sanitario, Receta médica",
                is_approved_for_sale=True,
                approval_date=date(2020, 8, 1)
            ),
            RegulatoryCondition(
                product_id=next((p.id for p in products if p.sku == 'INS-HUMAN-R'), None),
                country="Peru",
                regulatory_body="DIGEMID",
                import_restrictions="Medicamento de control especial",
                special_handling_requirements="Refrigeración continua",
                distribution_restrictions="Requiere prescripción médica",
                required_documentation="Registro DIGEMID, Receta médica",
                is_approved_for_sale=True,
                approval_date=date(2020, 6, 1)
            ),
        ]
        
        db.session.add_all(regulatory_conditions)
        db.session.commit()
        print(f"✅ Created {len(regulatory_conditions)} regulatory conditions")
        
        print("\n📊 Resumen de datos:")
        print(f"  Proveedores: {len(suppliers)}")
        print(f"  Productos: {len(products)}")
        print(f"  Certificaciones: {len(certifications)}")
        print(f"  Condiciones regulatorias: {len(regulatory_conditions)}")
        print("\n✅ Seed completado exitosamente!")

if __name__ == '__main__':
    seed_data()
