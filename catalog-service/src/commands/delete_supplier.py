from src.models.supplier import Supplier
from src.session import db
from src.errors.errors import ApiError, ValidationError, NotFoundError
from sqlalchemy.exc import IntegrityError


class DeleteSupplier:
    def __init__(self, supplier_id):
        self.supplier_id = supplier_id
        self.supplier = self._get_supplier()

    def _get_supplier(self):
        if not isinstance(self.supplier_id, int) or self.supplier_id <= 0:
            raise ValidationError('Supplier ID must be a positive integer')

        supplier = Supplier.query.filter_by(id=self.supplier_id).first()
        if not supplier:
            raise NotFoundError(f"Supplier with ID '{self.supplier_id}' not found")
        return supplier

    def execute(self):
        """Soft delete: set is_active=False"""
        try:
            db.session.refresh(self.supplier)

            supplier_data = self.supplier.to_dict()

            self.supplier.is_active = False

            db.session.commit()

            return {
                'message': f"Supplier '{self.supplier.name}' has been deactivated successfully",
                'deleted_supplier': supplier_data
            }

        except (ValidationError, ApiError, NotFoundError):
            db.session.rollback()
            raise
        except IntegrityError as e:
            db.session.rollback()
            msg = str(e.orig) if hasattr(e, 'orig') else str(e)
            raise ValidationError(f"Cannot deactivate supplier due to database constraints: {msg}")
        except Exception as e:
            db.session.rollback()
            raise ApiError(f"Error deleting supplier: {str(e)}", status_code=500)
