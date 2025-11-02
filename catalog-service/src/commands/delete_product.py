from src.models.product import Product
from src.session import db
from src.errors.errors import ApiError, ValidationError
from sqlalchemy.exc import IntegrityError


class DeleteProduct:
    def __init__(self, product_id):
        self.product_id = product_id
        self.product = self._get_product()
    
    def _get_product(self):
        """Get product by ID"""
        if not isinstance(self.product_id, int) or self.product_id <= 0:
            raise ValidationError("Product ID must be a positive integer")
        
        product = Product.query.filter_by(id=self.product_id).first()
        if not product:
            raise ApiError(f"Product with ID '{self.product_id}' not found", status_code=404)
        return product
    
    def execute(self):
        """Delete product (soft delete by default, or hard delete)"""
        try:
            # Refresh product state to get current database values
            db.session.refresh(self.product)
            
            # Store product data for response
            product_data = self.product.to_dict()
            
            # Perform soft delete by setting is_active to False
            # This is safer than hard delete as it preserves data integrity
            self.product.is_active = False
            self.product.is_discontinued = True
            
            db.session.commit()
            
            return {
                'message': f"Product '{self.product.sku}' has been deactivated successfully",
                'deleted_product': product_data
            }
            
        except (ValidationError, ApiError):
            db.session.rollback()
            raise
        except IntegrityError as e:
            db.session.rollback()
            # Handle database constraint violations during soft delete
            error_message = str(e.orig) if hasattr(e, 'orig') else str(e)
            raise ValidationError(f"Cannot deactivate product due to database constraints: {error_message}")
        except Exception as e:
            db.session.rollback()
            raise ApiError(f"Error deleting product: {str(e)}", status_code=500)
    
    def execute_hard_delete(self):
        """Perform hard delete (use with caution)"""
        try:
            # Store product data for response
            product_data = self.product.to_dict()
            
            # Hard delete - removes from database completely
            db.session.delete(self.product)
            db.session.commit()
            
            return {
                'message': f"Product '{self.product.sku}' has been permanently deleted",
                'deleted_product': product_data
            }
            
        except (ValidationError, ApiError):
            db.session.rollback()
            raise
        except IntegrityError as e:
            db.session.rollback()
            # Handle database constraint violations during hard delete
            error_message = str(e.orig) if hasattr(e, 'orig') else str(e)
            if 'FOREIGN KEY constraint failed' in error_message or 'foreign key' in error_message.lower():
                raise ValidationError(f"Cannot delete product '{self.product.sku}' because it is referenced by other records. Consider soft delete instead.")
            else:
                raise ValidationError(f"Cannot delete product due to database constraints: {error_message}")
        except Exception as e:
            db.session.rollback()
            raise ApiError(f"Error permanently deleting product: {str(e)}", status_code=500)