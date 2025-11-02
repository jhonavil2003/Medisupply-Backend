from src.models.product import Product
from src.errors.errors import NotFoundError

class GetProductById:    
    def __init__(self, product_id):
        if not product_id:
            raise ValueError("Product ID is required")
        if not isinstance(product_id, int) or product_id <= 0:
            raise ValueError("Product ID must be a positive integer")
        self.product_id = product_id
    
    def execute(self):
        product = Product.query.filter_by(id=self.product_id).first()
        
        if not product:
            raise NotFoundError(
                f"Product with ID '{self.product_id}' not found",
                payload={'product_id': self.product_id}
            )
        
        return product.to_dict_detailed()