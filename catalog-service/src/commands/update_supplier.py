from src.models.supplier import Supplier
from src.session import db
from src.errors.errors import ValidationError, NotFoundError, ApiError
from sqlalchemy.exc import IntegrityError


class UpdateSupplier:
    def __init__(self, supplier_id, data):
        self.supplier_id = supplier_id
        self.data = data or {}
        self.supplier = self._get_supplier()

    def _get_supplier(self):
        if not isinstance(self.supplier_id, int) or self.supplier_id <= 0:
            raise ValidationError('Supplier ID must be a positive integer')

        supplier = Supplier.query.filter_by(id=self.supplier_id).first()
        if not supplier:
            raise NotFoundError(f"Supplier with ID '{self.supplier_id}' not found")
        return supplier

    def execute(self):
        try:
            # Update allowed fields
            updatable = [
                'name', 'legal_name', 'tax_id', 'email', 'phone', 'website',
                'address_line1', 'address_line2', 'city', 'state', 'country', 'postal_code',
                'payment_terms', 'credit_limit', 'currency', 'is_certified',
                'certification_date', 'certification_expiry', 'is_active'
            ]

            # Handle nested address object if present
            address = self.data.get('address')
            if address and isinstance(address, dict):
                # Map address fields from nested structure
                if 'line1' in address:
                    setattr(self.supplier, 'address_line1', address.get('line1'))
                if 'line2' in address:
                    setattr(self.supplier, 'address_line2', address.get('line2'))
                if 'city' in address:
                    setattr(self.supplier, 'city', address.get('city'))
                if 'state' in address:
                    setattr(self.supplier, 'state', address.get('state'))
                if 'country' in address:
                    setattr(self.supplier, 'country', address.get('country'))
                if 'postal_code' in address:
                    setattr(self.supplier, 'postal_code', address.get('postal_code'))

            # Handle flat structure fields (backward compatibility)
            for k in updatable:
                if k in self.data:
                    setattr(self.supplier, k, self.data.get(k))

            db.session.commit()

            return self.supplier.to_dict()

        except IntegrityError as e:
            db.session.rollback()
            msg = str(e.orig) if hasattr(e, 'orig') else str(e)
            if 'unique' in msg.lower() or 'duplicate' in msg.lower():
                raise ValidationError('Unique constraint violation')
            raise ValidationError(f'Database error: {msg}')
        except (ValidationError, NotFoundError):
            db.session.rollback()
            raise
        except Exception as e:
            db.session.rollback()
            raise ApiError(f"Error updating supplier: {str(e)}", status_code=500)
