from src.models.supplier import Supplier
from src.session import db
from src.errors.errors import ValidationError, ApiError
from sqlalchemy.exc import IntegrityError


class CreateSupplier:
    def __init__(self, data):
        self.data = data or {}
        self._validate()

    def _validate(self):
        required = ['name', 'legal_name', 'tax_id', 'country']
        for f in required:
            if f not in self.data or not str(self.data.get(f)).strip():
                raise ValidationError(f"Field '{f}' is required")

        # tax_id uniqueness will be enforced by DB; additional checks can be added if needed

    def execute(self):
        try:
            supplier = Supplier(
                name=self.data.get('name'),
                legal_name=self.data.get('legal_name'),
                tax_id=self.data.get('tax_id'),
                email=self.data.get('email'),
                phone=self.data.get('phone'),
                website=self.data.get('website'),
                address_line1=self.data.get('address_line1'),
                address_line2=self.data.get('address_line2'),
                city=self.data.get('city'),
                state=self.data.get('state'),
                country=self.data.get('country'),
                postal_code=self.data.get('postal_code'),
                payment_terms=self.data.get('payment_terms'),
                credit_limit=self.data.get('credit_limit'),
                currency=self.data.get('currency'),
                is_certified=self.data.get('is_certified', False),
                certification_date=self.data.get('certification_date'),
                certification_expiry=self.data.get('certification_expiry'),
                is_active=self.data.get('is_active', True)
            )

            db.session.add(supplier)
            db.session.commit()

            return supplier.to_dict()

        except IntegrityError as e:
            db.session.rollback()
            # Try to provide a helpful message
            msg = str(e.orig) if hasattr(e, 'orig') else str(e)
            if 'unique' in msg.lower() or 'duplicate' in msg.lower():
                raise ValidationError('Supplier with provided unique field already exists')
            raise ValidationError(f'Database error: {msg}')
        except ValidationError:
            db.session.rollback()
            raise
        except Exception as e:
            db.session.rollback()
            raise ApiError(f"Error creating supplier: {str(e)}", status_code=500)
