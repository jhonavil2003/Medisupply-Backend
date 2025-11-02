from src.models.product import Product
from src.models.supplier import Supplier
from src.session import db
from src.errors.errors import ValidationError, ApiError
from decimal import Decimal
from sqlalchemy.exc import IntegrityError


class CreateProduct:
    def __init__(self, data):
        self.data = data
        self._validate_data()
    
    def _validate_data(self):
        """Validate input data for product creation"""
        required_fields = ['sku', 'name', 'category', 'unit_price', 'unit_of_measure', 'supplier_id']
        
        for field in required_fields:
            if field not in self.data or (self.data[field] is None or (isinstance(self.data[field], str) and not self.data[field].strip())):
                raise ValidationError(f"Field '{field}' is required")
        
        # Validate SKU uniqueness
        existing_product = Product.query.filter_by(sku=self.data['sku']).first()
        if existing_product:
            raise ValidationError(f"Product with SKU '{self.data['sku']}' already exists")
        
        # Validate supplier exists
        supplier = Supplier.query.get(self.data['supplier_id'])
        if not supplier:
            raise ValidationError(f"Supplier with ID '{self.data['supplier_id']}' not found")
        
        # Validate numeric fields
        try:
            if 'unit_price' in self.data:
                price = float(self.data['unit_price'])
                if price <= 0:
                    raise ValidationError("Unit price must be greater than zero")
            if 'weight_kg' in self.data and self.data['weight_kg'] is not None:
                float(self.data['weight_kg'])
        except (ValueError, TypeError):
            raise ValidationError("Invalid numeric values provided")
    
    def execute(self):
        """Create a new product"""
        try:
            product = Product(
                sku=self.data['sku'],
                name=self.data['name'],
                description=self.data.get('description', ''),
                category=self.data['category'],
                subcategory=self.data.get('subcategory'),
                unit_price=Decimal(str(self.data['unit_price'])),
                currency=self.data.get('currency', 'USD'),
                unit_of_measure=self.data['unit_of_measure'],
                supplier_id=self.data['supplier_id'],
                requires_cold_chain=self.data.get('requires_cold_chain', False),
                storage_temperature_min=Decimal(str(self.data['storage_temperature_min'])) if self.data.get('storage_temperature_min') else None,
                storage_temperature_max=Decimal(str(self.data['storage_temperature_max'])) if self.data.get('storage_temperature_max') else None,
                storage_humidity_max=Decimal(str(self.data['storage_humidity_max'])) if self.data.get('storage_humidity_max') else None,
                sanitary_registration=self.data.get('sanitary_registration'),
                requires_prescription=self.data.get('requires_prescription', False),
                regulatory_class=self.data.get('regulatory_class'),
                weight_kg=Decimal(str(self.data['weight_kg'])) if self.data.get('weight_kg') else None,
                length_cm=Decimal(str(self.data['length_cm'])) if self.data.get('length_cm') else None,
                width_cm=Decimal(str(self.data['width_cm'])) if self.data.get('width_cm') else None,
                height_cm=Decimal(str(self.data['height_cm'])) if self.data.get('height_cm') else None,
                is_active=self.data.get('is_active', True),
                is_discontinued=self.data.get('is_discontinued', False),
                manufacturer=self.data.get('manufacturer'),
                country_of_origin=self.data.get('country_of_origin'),
                barcode=self.data.get('barcode'),
                image_url=self.data.get('image_url')
            )
            
            db.session.add(product)
            db.session.commit()
            
            return product.to_dict()
            
        except (ValidationError, ApiError):
            db.session.rollback()
            raise
        except IntegrityError as e:
            db.session.rollback()
            # Handle database constraint violations (should return 400, not 500)
            error_message = str(e.orig) if hasattr(e, 'orig') else str(e)
            if 'UNIQUE constraint failed' in error_message or 'duplicate key' in error_message.lower():
                if 'sku' in error_message.lower():
                    raise ValidationError(f"Product with SKU '{self.data.get('sku')}' already exists")
                else:
                    raise ValidationError("A product with this information already exists")
            elif 'NOT NULL constraint failed' in error_message or 'null value' in error_message.lower():
                raise ValidationError("Required field cannot be null")
            elif 'FOREIGN KEY constraint failed' in error_message or 'foreign key' in error_message.lower():
                raise ValidationError("Invalid supplier ID provided")
            else:
                raise ValidationError(f"Database constraint violation: {error_message}")
        except Exception as e:
            db.session.rollback()
            raise ApiError(f"Error creating product: {str(e)}", status_code=500)