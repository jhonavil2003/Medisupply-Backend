"""
Shared seed data constants for all microservices.
This ensures data consistency across catalog, logistics, and sales services.
"""
from datetime import date
from decimal import Decimal

# ============================================================================
# SUPPLIERS DATA
# ============================================================================
SUPPLIERS_DATA = [
    {
        'id': 1,
        'name': "MedEquip Solutions",
        'legal_name': "MedEquip Solutions S.A.S.",
        'tax_id': "NIT-900123456",
        'email': "contact@medequip.com",
        'phone': "+57-1-3001234",
        'country': "Colombia",
        'city': "Bogotá",
        'is_certified': True,
        'certification_date': date(2023, 1, 15),
        'certification_expiry': date(2025, 1, 15),
        'is_active': True
    },
    {
        'id': 2,
        'name': "PharmaTech International",
        'legal_name': "PharmaTech International Inc.",
        'tax_id': "NIT-900234567",
        'email': "sales@pharmatech.com",
        'phone': "+1-305-5551234",
        'country': "USA",
        'city': "Miami",
        'is_certified': True,
        'certification_date': date(2022, 6, 1),
        'certification_expiry': date(2024, 6, 1),
        'is_active': True
    },
    {
        'id': 3,
        'name': "BioMedical Supplies",
        'legal_name': "BioMedical Supplies LTDA",
        'tax_id': "RUC-20567890123",
        'email': "info@biomedical.pe",
        'phone': "+51-1-4567890",
        'country': "Peru",
        'city': "Lima",
        'is_certified': True,
        'certification_date': date(2023, 3, 10),
        'certification_expiry': date(2025, 3, 10),
        'is_active': True
    }
]

# ============================================================================
# PRODUCTS DATA (Master Product Catalog)
# ============================================================================
PRODUCTS_DATA = [
    # Jeringas
    {
        'sku': 'JER-001',
        'name': 'Jeringa desechable 3ml con aguja',
        'description': 'Jeringa estéril desechable de 3ml con aguja calibre 21G x 1½',
        'category': 'Instrumental',
        'subcategory': 'Jeringas',
        'unit_price': Decimal('0.35'),
        'currency': 'USD',
        'unit_of_measure': 'unidad',
        'supplier_id': 1,
        'requires_cold_chain': False,
        'sanitary_registration': 'INVIMA-2021-0001234',
        'requires_prescription': False,
        'regulatory_class': 'Clase I',
        'weight_kg': Decimal('0.015'),
        'manufacturer': 'MedEquip Manufacturing',
        'country_of_origin': 'Colombia',
        'barcode': '7501234567890',
        'is_active': True
    },
    {
        'sku': 'JER-005',
        'name': 'Jeringa desechable 5ml sin aguja',
        'description': 'Jeringa estéril desechable de 5ml sin aguja, con escala graduada',
        'category': 'Instrumental',
        'subcategory': 'Jeringas',
        'unit_price': Decimal('0.28'),
        'currency': 'USD',
        'unit_of_measure': 'unidad',
        'supplier_id': 1,
        'requires_cold_chain': False,
        'sanitary_registration': 'INVIMA-2021-0001235',
        'requires_prescription': False,
        'regulatory_class': 'Clase I',
        'weight_kg': Decimal('0.012'),
        'manufacturer': 'MedEquip Manufacturing',
        'country_of_origin': 'Colombia',
        'barcode': '7501234567891',
        'is_active': True
    },
    {
        'sku': 'JER-010',
        'name': 'Jeringa desechable 10ml con aguja',
        'description': 'Jeringa estéril desechable de 10ml con aguja calibre 22G x 1',
        'category': 'Instrumental',
        'subcategory': 'Jeringas',
        'unit_price': Decimal('0.45'),
        'currency': 'USD',
        'unit_of_measure': 'unidad',
        'supplier_id': 1,
        'requires_cold_chain': False,
        'sanitary_registration': 'INVIMA-2021-0001236',
        'requires_prescription': False,
        'regulatory_class': 'Clase I',
        'weight_kg': Decimal('0.020'),
        'manufacturer': 'MedEquip Manufacturing',
        'country_of_origin': 'Colombia',
        'barcode': '7501234567892',
        'is_active': True
    },
    # Guantes
    {
        'sku': 'GLV-LAT-M',
        'name': 'Guantes de látex talla M',
        'description': 'Guantes de examinación de látex, no estériles, talla mediana, caja x 100 unidades',
        'category': 'Protección Personal',
        'subcategory': 'Guantes',
        'unit_price': Decimal('8.50'),
        'currency': 'USD',
        'unit_of_measure': 'caja',
        'supplier_id': 2,
        'requires_cold_chain': False,
        'sanitary_registration': 'FDA-510K-123456',
        'requires_prescription': False,
        'regulatory_class': 'Clase I',
        'weight_kg': Decimal('0.450'),
        'manufacturer': 'PharmaTech Manufacturing',
        'country_of_origin': 'USA',
        'barcode': '7502345678901',
        'is_active': True
    },
    {
        'sku': 'GLV-NIL-L',
        'name': 'Guantes de nitrilo talla L',
        'description': 'Guantes de examinación de nitrilo, sin polvo, talla grande, caja x 100 unidades',
        'category': 'Protección Personal',
        'subcategory': 'Guantes',
        'unit_price': Decimal('12.00'),
        'currency': 'USD',
        'unit_of_measure': 'caja',
        'supplier_id': 2,
        'requires_cold_chain': False,
        'sanitary_registration': 'FDA-510K-123457',
        'requires_prescription': False,
        'regulatory_class': 'Clase I',
        'weight_kg': Decimal('0.480'),
        'manufacturer': 'PharmaTech Manufacturing',
        'country_of_origin': 'USA',
        'barcode': '7502345678902',
        'is_active': True
    },
    # Medicamentos (requieren cadena de frío)
    {
        'sku': 'VAC-COVID-PF',
        'name': 'Vacuna COVID-19 Pfizer',
        'description': 'Vacuna mRNA contra COVID-19, vial multidosis (6 dosis)',
        'category': 'Medicamentos',
        'subcategory': 'Vacunas',
        'unit_price': Decimal('19.50'),
        'currency': 'USD',
        'unit_of_measure': 'vial',
        'supplier_id': 2,
        'requires_cold_chain': True,
        'storage_temperature_min': -80,
        'storage_temperature_max': -60,
        'sanitary_registration': 'FDA-BLA-125742',
        'requires_prescription': True,
        'regulatory_class': 'Clase III',
        'weight_kg': Decimal('0.050'),
        'manufacturer': 'Pfizer Inc.',
        'country_of_origin': 'USA',
        'barcode': '7503456789012',
        'is_active': True
    },
    {
        'sku': 'INS-HUMAN-R',
        'name': 'Insulina Humana Regular 100UI/ml',
        'description': 'Insulina humana de acción rápida, vial de 10ml',
        'category': 'Medicamentos',
        'subcategory': 'Insulinas',
        'unit_price': Decimal('24.00'),
        'currency': 'USD',
        'unit_of_measure': 'vial',
        'supplier_id': 3,
        'requires_cold_chain': True,
        'storage_temperature_min': 2,
        'storage_temperature_max': 8,
        'sanitary_registration': 'DIGEMID-2020-5678',
        'requires_prescription': True,
        'regulatory_class': 'Clase II',
        'weight_kg': Decimal('0.080'),
        'manufacturer': 'BioMedical Labs',
        'country_of_origin': 'Peru',
        'barcode': '7504567890123',
        'is_active': True
    },
    # Equipos médicos
    {
        'sku': 'OX-PULSE-01',
        'name': 'Oxímetro de pulso digital',
        'description': 'Oxímetro de pulso portátil con pantalla LED, incluye funda y baterías',
        'category': 'Equipos Médicos',
        'subcategory': 'Monitoreo',
        'unit_price': Decimal('35.00'),
        'currency': 'USD',
        'unit_of_measure': 'unidad',
        'supplier_id': 3,
        'requires_cold_chain': False,
        'sanitary_registration': 'CE-0123',
        'requires_prescription': False,
        'regulatory_class': 'Clase IIa',
        'weight_kg': Decimal('0.150'),
        'length_cm': Decimal('6.5'),
        'width_cm': Decimal('4.0'),
        'height_cm': Decimal('3.5'),
        'manufacturer': 'MedTech Devices',
        'country_of_origin': 'China',
        'barcode': '7505678901234',
        'is_active': True
    },
    {
        'sku': 'BP-MON-AUTO',
        'name': 'Tensiómetro digital automático',
        'description': 'Monitor de presión arterial digital automático de brazo, con memoria para 2 usuarios',
        'category': 'Equipos Médicos',
        'subcategory': 'Monitoreo',
        'unit_price': Decimal('45.00'),
        'currency': 'USD',
        'unit_of_measure': 'unidad',
        'supplier_id': 3,
        'requires_cold_chain': False,
        'sanitary_registration': 'CE-0124',
        'requires_prescription': False,
        'regulatory_class': 'Clase IIa',
        'weight_kg': Decimal('0.450'),
        'length_cm': Decimal('15.0'),
        'width_cm': Decimal('12.0'),
        'height_cm': Decimal('8.0'),
        'manufacturer': 'HealthCare Electronics',
        'country_of_origin': 'Japan',
        'barcode': '7506789012345',
        'is_active': True
    },
    # Protección Personal
    {
        'sku': 'MASK-N95',
        'name': 'Mascarilla N95 respirador',
        'description': 'Mascarilla respirador N95, certificada NIOSH, caja x 20 unidades',
        'category': 'Protección Personal',
        'subcategory': 'Mascarillas',
        'unit_price': Decimal('28.00'),
        'currency': 'USD',
        'unit_of_measure': 'caja',
        'supplier_id': 2,
        'requires_cold_chain': False,
        'sanitary_registration': 'NIOSH-TC-84A-9315',
        'requires_prescription': False,
        'regulatory_class': 'Clase II',
        'weight_kg': Decimal('0.180'),
        'manufacturer': '3M Healthcare',
        'country_of_origin': 'USA',
        'barcode': '7507890123456',
        'is_active': True
    },
    {
        'sku': 'THERM-DIG-01',
        'name': 'Termómetro digital infrarrojo',
        'description': 'Termómetro digital sin contacto, medición en 1 segundo',
        'category': 'Equipos Médicos',
        'subcategory': 'Diagnóstico',
        'unit_price': Decimal('22.00'),
        'currency': 'USD',
        'unit_of_measure': 'unidad',
        'supplier_id': 3,
        'requires_cold_chain': False,
        'sanitary_registration': 'CE-0125',
        'requires_prescription': False,
        'regulatory_class': 'Clase IIa',
        'weight_kg': Decimal('0.120'),
        'manufacturer': 'HealthCare Electronics',
        'country_of_origin': 'China',
        'barcode': '7508901234567',
        'is_active': True
    },
    {
        'sku': 'GAUZE-10X10',
        'name': 'Gasa estéril 10x10cm',
        'description': 'Gasa estéril de algodón, 10x10cm, paquete x 10 unidades',
        'category': 'Instrumental',
        'subcategory': 'Material de curación',
        'unit_price': Decimal('1.50'),
        'currency': 'USD',
        'unit_of_measure': 'paquete',
        'supplier_id': 1,
        'requires_cold_chain': False,
        'sanitary_registration': 'INVIMA-2021-0001237',
        'requires_prescription': False,
        'regulatory_class': 'Clase I',
        'weight_kg': Decimal('0.025'),
        'manufacturer': 'MedEquip Manufacturing',
        'country_of_origin': 'Colombia',
        'barcode': '7509012345678',
        'is_active': True
    },
    {
        'sku': 'ALCO-500ML',
        'name': 'Alcohol antiséptico 70% 500ml',
        'description': 'Alcohol etílico al 70%, uso externo, botella de 500ml',
        'category': 'Instrumental',
        'subcategory': 'Antisépticos',
        'unit_price': Decimal('3.50'),
        'currency': 'USD',
        'unit_of_measure': 'botella',
        'supplier_id': 1,
        'requires_cold_chain': False,
        'sanitary_registration': 'INVIMA-2021-0001238',
        'requires_prescription': False,
        'regulatory_class': 'Clase I',
        'weight_kg': Decimal('0.520'),
        'manufacturer': 'MedEquip Manufacturing',
        'country_of_origin': 'Colombia',
        'barcode': '7510123456789',
        'is_active': True
    },
    {
        'sku': 'BAND-ELAS-5CM',
        'name': 'Vendaje elástico 5cm x 5m',
        'description': 'Vendaje elástico de algodón, 5cm de ancho x 5m de largo',
        'category': 'Instrumental',
        'subcategory': 'Material de curación',
        'unit_price': Decimal('2.00'),
        'currency': 'USD',
        'unit_of_measure': 'unidad',
        'supplier_id': 1,
        'requires_cold_chain': False,
        'sanitary_registration': 'INVIMA-2021-0001239',
        'requires_prescription': False,
        'regulatory_class': 'Clase I',
        'weight_kg': Decimal('0.040'),
        'manufacturer': 'MedEquip Manufacturing',
        'country_of_origin': 'Colombia',
        'barcode': '7511234567890',
        'is_active': True
    }
]

# ============================================================================
# DISTRIBUTION CENTERS DATA
# ============================================================================
DISTRIBUTION_CENTERS_DATA = [
    {
        'code': 'CEDIS-BOG',
        'name': 'Centro de Distribución Bogotá',
        'address': 'Calle 100 # 15-20',
        'city': 'Bogotá',
        'state': 'Cundinamarca',
        'country': 'Colombia',
        'postal_code': '110111',
        'phone': '+57 1 234 5678',
        'email': 'bogota@medisupply.com',
        'manager_name': 'Carlos Rodríguez',
        'capacity_m3': Decimal('5000.00'),
        'is_active': True,
        'supports_cold_chain': True
    },
    {
        'code': 'CEDIS-MED',
        'name': 'Centro de Distribución Medellín',
        'address': 'Carrera 50 # 30-15',
        'city': 'Medellín',
        'state': 'Antioquia',
        'country': 'Colombia',
        'postal_code': '050001',
        'phone': '+57 4 567 8901',
        'email': 'medellin@medisupply.com',
        'manager_name': 'Ana María López',
        'capacity_m3': Decimal('3000.00'),
        'is_active': True,
        'supports_cold_chain': True
    },
    {
        'code': 'CEDIS-CALI',
        'name': 'Centro de Distribución Cali',
        'address': 'Avenida 6N # 25-40',
        'city': 'Cali',
        'state': 'Valle del Cauca',
        'country': 'Colombia',
        'postal_code': '760001',
        'phone': '+57 2 345 6789',
        'email': 'cali@medisupply.com',
        'manager_name': 'Jorge Martínez',
        'capacity_m3': Decimal('2500.00'),
        'is_active': True,
        'supports_cold_chain': False
    },
    {
        'code': 'CEDIS-BAQ',
        'name': 'Centro de Distribución Barranquilla',
        'address': 'Carrera 38 # 74-194',
        'city': 'Barranquilla',
        'state': 'Atlántico',
        'country': 'Colombia',
        'postal_code': '080001',
        'phone': '+57 5 678 9012',
        'email': 'barranquilla@medisupply.com',
        'manager_name': 'Patricia Gómez',
        'capacity_m3': Decimal('2000.00'),
        'is_active': True,
        'supports_cold_chain': True
    }
]

# ============================================================================
# CUSTOMERS DATA
# ============================================================================
CUSTOMERS_DATA = [
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
        'credit_limit': Decimal('50000000.00'),
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
        'credit_limit': Decimal('30000000.00'),
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
        'credit_limit': Decimal('20000000.00'),
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
        'credit_limit': Decimal('40000000.00'),
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
        'credit_limit': Decimal('60000000.00'),
        'credit_days': 90,
        'is_active': True
    }
]


# Helper function to get product by SKU
def get_product_by_sku(sku):
    """Get product data by SKU."""
    for product in PRODUCTS_DATA:
        if product['sku'] == sku:
            return product
    return None


# Helper function to get all product SKUs
def get_all_product_skus():
    """Get list of all product SKUs."""
    return [p['sku'] for p in PRODUCTS_DATA]
