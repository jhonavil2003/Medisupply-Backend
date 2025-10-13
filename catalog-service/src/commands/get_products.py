from src.models.product import Product
from src.session import db
from sqlalchemy import or_, and_

class GetProducts:
    def __init__(self, search=None, sku=None, category=None, subcategory=None,
                 supplier_id=None, is_active=True, requires_cold_chain=None,
                 page=1, per_page=20):
        self.search = search
        self.sku = sku
        self.category = category
        self.subcategory = subcategory
        self.supplier_id = supplier_id
        self.is_active = is_active
        self.requires_cold_chain = requires_cold_chain
        self.page = max(1, page)
        self.per_page = min(100, max(1, per_page))  # Max 100 items per page
    
    def execute(self):
        query = Product.query
        
        filters = []
        
        if self.is_active is not None:
            filters.append(Product.is_active == self.is_active)
        
        if self.requires_cold_chain is not None:
            filters.append(Product.requires_cold_chain == self.requires_cold_chain)
        
        if self.supplier_id:
            filters.append(Product.supplier_id == self.supplier_id)
        
        if self.category:
            filters.append(Product.category.ilike(f'%{self.category}%'))
        
        if self.subcategory:
            filters.append(Product.subcategory.ilike(f'%{self.subcategory}%'))
        
        if self.sku:
            filters.append(Product.sku.ilike(f'%{self.sku}%'))
        
        if self.search:
            search_filter = or_(
                Product.name.ilike(f'%{self.search}%'),
                Product.description.ilike(f'%{self.search}%'),
                Product.sku.ilike(f'%{self.search}%'),
                Product.barcode.ilike(f'%{self.search}%'),
                Product.manufacturer.ilike(f'%{self.search}%')
            )
            filters.append(search_filter)
        
        if filters:
            query = query.filter(and_(*filters))
        
        query = query.order_by(Product.name.asc())
        
        pagination = query.paginate(
            page=self.page,
            per_page=self.per_page,
            error_out=False
        )
        
        return {
            'products': [product.to_dict() for product in pagination.items],
            'pagination': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total_pages': pagination.pages,
                'total_items': pagination.total,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev,
            }
        }
