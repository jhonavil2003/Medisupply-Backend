from src.models.product import Product
from src.errors.errors import NotFoundError

class GetProductBySKU:    
    def __init__(self, sku):
        if not sku:
            raise ValueError("SKU is required")
        self.sku = sku.strip().upper()
    
    def execute(self):
        product = Product.query.filter_by(sku=self.sku).first()
        
        if not product:
            raise NotFoundError(
                f"Product with SKU '{self.sku}' not found",
                payload={'sku': self.sku}
            )
        
        return product.to_dict_detailed()
