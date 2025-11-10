from src.models.supplier import Supplier
from src.errors.errors import NotFoundError


class GetSupplierById:
    def __init__(self, supplier_id):
        if supplier_id is None:
            raise ValueError("Supplier ID is required")
        if not isinstance(supplier_id, int) or supplier_id <= 0:
            raise ValueError("Supplier ID must be a positive integer")
        self.supplier_id = supplier_id

    def execute(self):
        supplier = Supplier.query.filter_by(id=self.supplier_id).first()
        if not supplier:
            raise NotFoundError(f"Supplier with ID '{self.supplier_id}' not found", payload={'supplier_id': self.supplier_id})
        return supplier.to_dict()
