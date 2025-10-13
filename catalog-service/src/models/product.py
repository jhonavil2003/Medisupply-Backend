from src.session import db
from datetime import datetime

class Product(db.Model):
    __tablename__ = 'products'
    
    # Primary Key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Identificación del producto
    sku = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False, index=True)
    description = db.Column(db.Text)
    
    # Categorización
    category = db.Column(db.String(100), nullable=False, index=True)
    subcategory = db.Column(db.String(100))
    
    # Información comercial
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(3), default='USD')
    unit_of_measure = db.Column(db.String(20), nullable=False)  # unidad, caja, paquete
    
    # Proveedor
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=False)
    
    # Condiciones de almacenamiento
    requires_cold_chain = db.Column(db.Boolean, default=False)
    storage_temperature_min = db.Column(db.Numeric(5, 2))  # Celsius
    storage_temperature_max = db.Column(db.Numeric(5, 2))  # Celsius
    storage_humidity_max = db.Column(db.Numeric(5, 2))  # Porcentaje
    
    # Información regulatoria
    sanitary_registration = db.Column(db.String(100))
    requires_prescription = db.Column(db.Boolean, default=False)
    regulatory_class = db.Column(db.String(50))  # Clase I, IIa, IIb, III
    
    # Dimensiones y peso (para logística)
    weight_kg = db.Column(db.Numeric(10, 3))
    length_cm = db.Column(db.Numeric(10, 2))
    width_cm = db.Column(db.Numeric(10, 2))
    height_cm = db.Column(db.Numeric(10, 2))
    
    # Estado y disponibilidad
    is_active = db.Column(db.Boolean, default=True, index=True)
    is_discontinued = db.Column(db.Boolean, default=False)
    
    # Información adicional
    manufacturer = db.Column(db.String(255))
    country_of_origin = db.Column(db.String(100))
    barcode = db.Column(db.String(50))
    image_url = db.Column(db.String(500))
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = db.Column(db.String(100))
    
    # Relaciones
    supplier = db.relationship('Supplier', back_populates='products')
    certifications = db.relationship('Certification', back_populates='product', cascade='all, delete-orphan')
    regulatory_conditions = db.relationship('RegulatoryCondition', back_populates='product', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'sku': self.sku,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'subcategory': self.subcategory,
            'unit_price': float(self.unit_price) if self.unit_price else None,
            'currency': self.currency,
            'unit_of_measure': self.unit_of_measure,
            'supplier_id': self.supplier_id,
            'supplier_name': self.supplier.name if self.supplier else None,
            'requires_cold_chain': self.requires_cold_chain,
            'storage_conditions': {
                'temperature_min': float(self.storage_temperature_min) if self.storage_temperature_min else None,
                'temperature_max': float(self.storage_temperature_max) if self.storage_temperature_max else None,
                'humidity_max': float(self.storage_humidity_max) if self.storage_humidity_max else None,
            },
            'regulatory_info': {
                'sanitary_registration': self.sanitary_registration,
                'requires_prescription': self.requires_prescription,
                'regulatory_class': self.regulatory_class,
            },
            'physical_dimensions': {
                'weight_kg': float(self.weight_kg) if self.weight_kg else None,
                'length_cm': float(self.length_cm) if self.length_cm else None,
                'width_cm': float(self.width_cm) if self.width_cm else None,
                'height_cm': float(self.height_cm) if self.height_cm else None,
            },
            'manufacturer': self.manufacturer,
            'country_of_origin': self.country_of_origin,
            'barcode': self.barcode,
            'image_url': self.image_url,
            'is_active': self.is_active,
            'is_discontinued': self.is_discontinued,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def to_dict_detailed(self):
        """Convierte el producto a diccionario con información completa"""
        base_dict = self.to_dict()
        base_dict['certifications'] = [cert.to_dict() for cert in self.certifications]
        base_dict['regulatory_conditions'] = [rc.to_dict() for rc in self.regulatory_conditions]
        return base_dict
    
    def __repr__(self):
        return f'<Product {self.sku}: {self.name}>'
