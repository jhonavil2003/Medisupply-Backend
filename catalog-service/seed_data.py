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

def seed_data():
    app = create_app()
    
    with app.app_context():
        print("🗑️  Clearing existing data...")
        db.drop_all()
        db.create_all()
        
        print("Creating suppliers...")
        suppliers = [
            Supplier(
                name="MedEquip Solutions",
                legal_name="MedEquip Solutions S.A.S.",
                tax_id="NIT-900123456",
                email="contact@medequip.com",
                phone="+57-1-3001234",
                country="Colombia",
                city="Bogotá",
                is_certified=True,
                certification_date=date(2023, 1, 15),
                certification_expiry=date(2025, 1, 15),
                is_active=True
            ),
            Supplier(
                name="PharmaTech International",
                legal_name="PharmaTech International Inc.",
                tax_id="NIT-900234567",
                email="sales@pharmatech.com",
                phone="+1-305-5551234",
                country="USA",
                city="Miami",
                is_certified=True,
                certification_date=date(2022, 6, 1),
                certification_expiry=date(2024, 6, 1),
                is_active=True
            ),
            Supplier(
                name="BioMedical Supplies",
                legal_name="BioMedical Supplies LTDA",
                tax_id="RUC-20567890123",
                email="info@biomedical.pe",
                phone="+51-1-4567890",
                country="Peru",
                city="Lima",
                is_certified=True,
                certification_date=date(2023, 3, 10),
                certification_expiry=date(2025, 3, 10),
                is_active=True
            )
        ]
        
        db.session.add_all(suppliers)
        db.session.commit()
        print(f"✅ Created {len(suppliers)} suppliers")
        
        print("Creating products...")
        products = [
            # Jeringas
            Product(
                sku="JER-001",
                name="Jeringa desechable 3ml con aguja",
                description="Jeringa estéril desechable de 3ml con aguja calibre 21G x 1½",
                category="Instrumental",
                subcategory="Jeringas",
                unit_price=0.35,
                currency="USD",
                unit_of_measure="unidad",
                supplier_id=suppliers[0].id,
                requires_cold_chain=False,
                sanitary_registration="INVIMA-2021-0001234",
                requires_prescription=False,
                regulatory_class="Clase I",
                weight_kg=0.015,
                manufacturer="MedEquip Manufacturing",
                country_of_origin="Colombia",
                barcode="7501234567890",
                is_active=True
            ),
            Product(
                sku="JER-005",
                name="Jeringa desechable 5ml sin aguja",
                description="Jeringa estéril desechable de 5ml sin aguja, con escala graduada",
                category="Instrumental",
                subcategory="Jeringas",
                unit_price=0.28,
                currency="USD",
                unit_of_measure="unidad",
                supplier_id=suppliers[0].id,
                requires_cold_chain=False,
                sanitary_registration="INVIMA-2021-0001235",
                requires_prescription=False,
                regulatory_class="Clase I",
                weight_kg=0.012,
                manufacturer="MedEquip Manufacturing",
                country_of_origin="Colombia",
                barcode="7501234567891",
                is_active=True
            ),
            Product(
                sku="JER-010",
                name="Jeringa desechable 10ml con aguja",
                description="Jeringa estéril desechable de 10ml con aguja calibre 22G x 1",
                category="Instrumental",
                subcategory="Jeringas",
                unit_price=0.45,
                currency="USD",
                unit_of_measure="unidad",
                supplier_id=suppliers[0].id,
                requires_cold_chain=False,
                sanitary_registration="INVIMA-2021-0001236",
                requires_prescription=False,
                regulatory_class="Clase I",
                weight_kg=0.020,
                manufacturer="MedEquip Manufacturing",
                country_of_origin="Colombia",
                barcode="7501234567892",
                is_active=True
            ),
            # Guantes
            Product(
                sku="GLV-LAT-M",
                name="Guantes de látex talla M",
                description="Guantes de examinación de látex, no estériles, talla mediana, caja x 100 unidades",
                category="Protección Personal",
                subcategory="Guantes",
                unit_price=8.50,
                currency="USD",
                unit_of_measure="caja",
                supplier_id=suppliers[1].id,
                requires_cold_chain=False,
                sanitary_registration="FDA-510K-123456",
                requires_prescription=False,
                regulatory_class="Clase I",
                weight_kg=0.450,
                manufacturer="PharmaTech Manufacturing",
                country_of_origin="USA",
                barcode="7502345678901",
                is_active=True
            ),
            Product(
                sku="GLV-NIL-L",
                name="Guantes de nitrilo talla L",
                description="Guantes de examinación de nitrilo, sin polvo, talla grande, caja x 100 unidades",
                category="Protección Personal",
                subcategory="Guantes",
                unit_price=12.00,
                currency="USD",
                unit_of_measure="caja",
                supplier_id=suppliers[1].id,
                requires_cold_chain=False,
                sanitary_registration="FDA-510K-123457",
                requires_prescription=False,
                regulatory_class="Clase I",
                weight_kg=0.480,
                manufacturer="PharmaTech Manufacturing",
                country_of_origin="USA",
                barcode="7502345678902",
                is_active=True
            ),
            # Medicamentos (requieren cadena de frío)
            Product(
                sku="VAC-COVID-PF",
                name="Vacuna COVID-19 Pfizer",
                description="Vacuna mRNA contra COVID-19, vial multidosis (6 dosis)",
                category="Medicamentos",
                subcategory="Vacunas",
                unit_price=19.50,
                currency="USD",
                unit_of_measure="vial",
                supplier_id=suppliers[1].id,
                requires_cold_chain=True,
                storage_temperature_min=-80,
                storage_temperature_max=-60,
                sanitary_registration="FDA-BLA-125742",
                requires_prescription=True,
                regulatory_class="Clase III",
                weight_kg=0.050,
                manufacturer="Pfizer Inc.",
                country_of_origin="USA",
                barcode="7503456789012",
                is_active=True
            ),
            Product(
                sku="INS-HUMAN-R",
                name="Insulina Humana Regular 100UI/ml",
                description="Insulina humana de acción rápida, vial de 10ml",
                category="Medicamentos",
                subcategory="Insulinas",
                unit_price=24.00,
                currency="USD",
                unit_of_measure="vial",
                supplier_id=suppliers[2].id,
                requires_cold_chain=True,
                storage_temperature_min=2,
                storage_temperature_max=8,
                sanitary_registration="DIGEMID-2020-5678",
                requires_prescription=True,
                regulatory_class="Clase II",
                weight_kg=0.080,
                manufacturer="BioMedical Labs",
                country_of_origin="Peru",
                barcode="7504567890123",
                is_active=True
            ),
            # Equipos médicos
            Product(
                sku="OX-PULSE-01",
                name="Oxímetro de pulso digital",
                description="Oxímetro de pulso portátil con pantalla LED, incluye funda y baterías",
                category="Equipos Médicos",
                subcategory="Monitoreo",
                unit_price=35.00,
                currency="USD",
                unit_of_measure="unidad",
                supplier_id=suppliers[2].id,
                requires_cold_chain=False,
                sanitary_registration="CE-0123",
                requires_prescription=False,
                regulatory_class="Clase IIa",
                weight_kg=0.150,
                length_cm=6.5,
                width_cm=4.0,
                height_cm=3.5,
                manufacturer="MedTech Devices",
                country_of_origin="China",
                barcode="7505678901234",
                is_active=True
            ),
            Product(
                sku="BP-MON-AUTO",
                name="Tensiómetro digital automático",
                description="Monitor de presión arterial digital automático de brazo, con memoria para 2 usuarios",
                category="Equipos Médicos",
                subcategory="Monitoreo",
                unit_price=45.00,
                currency="USD",
                unit_of_measure="unidad",
                supplier_id=suppliers[2].id,
                requires_cold_chain=False,
                sanitary_registration="CE-0124",
                requires_prescription=False,
                regulatory_class="Clase IIa",
                weight_kg=0.450,
                length_cm=15.0,
                width_cm=12.0,
                height_cm=8.0,
                manufacturer="HealthCare Electronics",
                country_of_origin="Japan",
                barcode="7506789012345",
                is_active=True
            ),
            # Más productos de instrumental
            Product(
                sku="MASK-N95",
                name="Mascarilla N95 respirador",
                description="Mascarilla respirador N95, certificada NIOSH, caja x 20 unidades",
                category="Protección Personal",
                subcategory="Mascarillas",
                unit_price=28.00,
                currency="USD",
                unit_of_measure="caja",
                supplier_id=suppliers[1].id,
                requires_cold_chain=False,
                sanitary_registration="NIOSH-TC-84A-9315",
                requires_prescription=False,
                regulatory_class="Clase II",
                weight_kg=0.180,
                manufacturer="3M Healthcare",
                country_of_origin="USA",
                barcode="7507890123456",
                is_active=True
            ),
        ]
        
        db.session.add_all(products)
        db.session.commit()
        print(f"✅ Created {len(products)} products")
        
        # Create certifications
        print("Creating certifications...")
        certifications = [
            # Certifications for vaccine
            Certification(
                product_id=products[5].id,  # VAC-COVID-PF
                certification_type="FDA",
                certification_number="BLA-125742",
                issuing_authority="U.S. Food and Drug Administration",
                country="USA",
                issue_date=date(2020, 12, 11),
                expiry_date=date(2025, 12, 11),
                is_valid=True
            ),
            Certification(
                product_id=products[5].id,
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
                product_id=products[6].id,  # INS-HUMAN-R
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
        print("Creating regulatory conditions...")
        regulatory_conditions = [
            # Regulatory conditions for vaccine in different countries
            RegulatoryCondition(
                product_id=products[5].id,  # VAC-COVID-PF
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
                product_id=products[5].id,
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
                product_id=products[6].id,  # INS-HUMAN-R
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
                product_id=products[6].id,
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

if __name__ == '__main__':
    seed_data()
