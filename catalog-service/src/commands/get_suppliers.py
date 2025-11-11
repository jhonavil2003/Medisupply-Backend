from src.models.supplier import Supplier
from src.session import db
from sqlalchemy import or_, and_


class GetSuppliers:
    def __init__(self, search=None, name=None, country=None, is_active=None, page=1, per_page=20):
        self.search = search
        self.name = name
        self.country = country
        self.is_active = is_active
        self.page = max(1, page)
        self.per_page = min(100, max(1, per_page))

    def execute(self):
        query = Supplier.query

        filters = []

        if self.is_active is not None:
            filters.append(Supplier.is_active == self.is_active)

        if self.name:
            filters.append(Supplier.name.ilike(f"%{self.name}%"))

        if self.country:
            filters.append(Supplier.country.ilike(f"%{self.country}%"))

        if self.search:
            search_filter = or_(
                Supplier.name.ilike(f"%{self.search}%"),
                Supplier.legal_name.ilike(f"%{self.search}%"),
                Supplier.tax_id.ilike(f"%{self.search}%")
            )
            filters.append(search_filter)

        if filters:
            query = query.filter(and_(*filters))

        query = query.order_by(Supplier.name.asc())

        pagination = query.paginate(page=self.page, per_page=self.per_page, error_out=False)

        return {
            'suppliers': [s.to_dict() for s in pagination.items],
            'pagination': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total_pages': pagination.pages,
                'total_items': pagination.total,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }
