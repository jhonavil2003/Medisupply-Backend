from src.models.product import Product
from src.models.supplier import Supplier
from src.session import db
from src.errors.errors import ValidationError, ApiError
from decimal import Decimal
from sqlalchemy.exc import IntegrityError


class UpdateProduct:
    def __init__(self, product_id, data):
        self.product_id = product_id
        self.data = data
        self.product = self._get_product()
        self._validate_data()
    
    def _get_product(self):
        """Get product by ID"""
        if not isinstance(self.product_id, int) or self.product_id <= 0:
            raise ValidationError("Product ID must be a positive integer")
        
        product = Product.query.filter_by(id=self.product_id).first()
        if not product:
            raise ApiError(f"Product with ID '{self.product_id}' not found", status_code=404)
        return product
    
    def _validate_data(self):
        """Validate input data for product update"""
        # If SKU is being changed, validate uniqueness
        if 'sku' in self.data and self.data['sku'] != self.product.sku:
            existing_product = Product.query.filter_by(sku=self.data['sku']).first()
            if existing_product:
                raise ValidationError(f"Product with SKU '{self.data['sku']}' already exists")
        
        # Validate supplier exists if being updated
        if 'supplier_id' in self.data:
            supplier = Supplier.query.get(self.data['supplier_id'])
            if not supplier:
                raise ValidationError(f"Supplier with ID '{self.data['supplier_id']}' not found")
        
        # Validate numeric fields
        numeric_fields = ['unit_price', 'weight_kg', 'length_cm', 'width_cm', 'height_cm',
                         'storage_temperature_min', 'storage_temperature_max', 'storage_humidity_max']
        
        for field in numeric_fields:
            if field in self.data and self.data[field] is not None:
                try:
                    value = float(self.data[field])
                    # Special validation for unit_price - must be positive
                    if field == 'unit_price' and value <= 0:
                        raise ValidationError("Unit price must be greater than zero")
                except (ValueError, TypeError):
                    raise ValidationError(f"Invalid numeric value for field '{field}'")
    
    def execute(self):
        """Update product with provided data"""
        try:
            # Update fields that are provided (except SKU which should not be changed)
            for field, value in self.data.items():
                if field == 'sku':
                    continue  # Skip SKU updates for security
                if hasattr(self.product, field):
                    # Trim string fields
                    if isinstance(value, str):
                        value = value.strip()
                    
                    # Convert numeric fields to Decimal
                    if field in ['unit_price', 'weight_kg', 'length_cm', 'width_cm', 'height_cm',
                               'storage_temperature_min', 'storage_temperature_max', 'storage_humidity_max']:
                        if value is not None:
                            value = Decimal(str(value))
                    
                    setattr(self.product, field, value)
            
            db.session.commit()
            
            return self.product.to_dict()
            
        except (ValidationError, ApiError):
            db.session.rollback()
            raise
        except IntegrityError as e:
            db.session.rollback()
            # Handle database constraint violations (should return 400, not 500)
            error_message = str(e.orig) if hasattr(e, 'orig') else str(e)
            if 'UNIQUE constraint failed' in error_message or 'duplicate key' in error_message.lower():
                if 'sku' in error_message.lower():
                    raise ValidationError(f"Another product with SKU '{self.data.get('sku')}' already exists")
                else:
                    raise ValidationError("A product with this information already exists")
            elif 'FOREIGN KEY constraint failed' in error_message or 'foreign key' in error_message.lower():
                raise ValidationError("Invalid supplier ID provided")
            else:
                raise ValidationError(f"Database constraint violation: {error_message}")
        except Exception as e:
            db.session.rollback()
            raise ApiError(f"Error updating product: {str(e)}", status_code=500)