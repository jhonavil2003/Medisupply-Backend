from src.models.inventory import Inventory
from src.models.distribution_center import DistributionCenter
from src.session import db
from sqlalchemy import and_, or_

class GetStockLevels:
    def __init__(self, product_sku=None, product_skus=None, distribution_center_id=None, 
                 only_available=False, include_reserved=True, include_in_transit=False):
        self.product_sku = product_sku
        self.product_skus = product_skus or []
        self.distribution_center_id = distribution_center_id
        self.only_available = only_available
        self.include_reserved = include_reserved
        self.include_in_transit = include_in_transit
    
    def execute(self):
        query = Inventory.query.join(DistributionCenter)
        
        filters = []
        
        if self.product_sku:
            filters.append(Inventory.product_sku == self.product_sku.upper())
        
        if self.product_skus:
            skus_upper = [sku.upper() for sku in self.product_skus]
            filters.append(Inventory.product_sku.in_(skus_upper))
        
        if self.distribution_center_id:
            filters.append(Inventory.distribution_center_id == self.distribution_center_id)
        
        filters.append(DistributionCenter.is_active == True)
        
        if self.only_available:
            filters.append(Inventory.quantity_available > 0)
        
        if filters:
            query = query.filter(and_(*filters))
        
        query = query.order_by(
            Inventory.product_sku.asc(),
            DistributionCenter.name.asc()
        )
        
        inventory_items = query.all()
        
        if self.product_sku or (self.product_skus and len(self.product_skus) == 1):
            return self._format_single_product_response(inventory_items)
        else:
            return self._format_multiple_products_response(inventory_items)
    
    def _format_single_product_response(self, inventory_items):
        if not inventory_items:
            return {
                'product_sku': self.product_sku or (self.product_skus[0] if self.product_skus else None),
                'total_available': 0,
                'total_reserved': 0,
                'total_in_transit': 0,
                'distribution_centers': []
            }
        
        product_sku = inventory_items[0].product_sku
        total_quantity_available = sum(item.quantity_available for item in inventory_items)
        total_reserved = sum(item.quantity_reserved for item in inventory_items)
        total_in_transit = sum(item.quantity_in_transit for item in inventory_items)
        
        # Stock realmente disponible para venta = quantity_available - quantity_reserved
        total_available_for_sale = total_quantity_available - total_reserved
        
        centers = []
        for item in inventory_items:
            # Stock disponible para venta en este centro
            available_for_sale = item.quantity_available - item.quantity_reserved
            
            center_data = {
                'distribution_center_id': item.distribution_center_id,
                'distribution_center_code': item.distribution_center.code,
                'distribution_center_name': item.distribution_center.name,
                'city': item.distribution_center.city,
                'quantity_available': available_for_sale,  # Stock disponible para venta
                'quantity_physical': item.quantity_available,  # Stock físico en almacén
                'is_low_stock': item.is_low_stock,
                'is_out_of_stock': available_for_sale <= 0,  # Sin stock si no hay disponible para venta
            }
            
            if self.include_reserved:
                center_data['quantity_reserved'] = item.quantity_reserved
            
            if self.include_in_transit:
                center_data['quantity_in_transit'] = item.quantity_in_transit
            
            centers.append(center_data)
        
        return {
            'product_sku': product_sku,
            'total_available': total_available_for_sale,  # Stock disponible para venta
            'total_physical': total_quantity_available,  # Stock físico total
            'total_reserved': total_reserved if self.include_reserved else None,
            'total_in_transit': total_in_transit if self.include_in_transit else None,
            'distribution_centers': centers
        }
    
    def _format_multiple_products_response(self, inventory_items):
        products_dict = {}
        
        for item in inventory_items:
            sku = item.product_sku
            
            if sku not in products_dict:
                products_dict[sku] = {
                    'product_sku': sku,
                    'total_available': 0,
                    'total_physical': 0,
                    'total_reserved': 0,
                    'total_in_transit': 0,
                    'distribution_centers': []
                }
            
            # Stock disponible para venta = quantity_available - quantity_reserved
            available_for_sale = item.quantity_available - item.quantity_reserved
            
            products_dict[sku]['total_available'] += available_for_sale
            products_dict[sku]['total_physical'] += item.quantity_available
            products_dict[sku]['total_reserved'] += item.quantity_reserved
            products_dict[sku]['total_in_transit'] += item.quantity_in_transit
            
            center_data = {
                'distribution_center_id': item.distribution_center_id,
                'distribution_center_code': item.distribution_center.code,
                'distribution_center_name': item.distribution_center.name,
                'city': item.distribution_center.city,
                'quantity_available': available_for_sale,  # Stock disponible para venta
                'quantity_physical': item.quantity_available,  # Stock físico en almacén
                'is_low_stock': item.is_low_stock,
                'is_out_of_stock': available_for_sale <= 0,
            }
            
            if self.include_reserved:
                center_data['quantity_reserved'] = item.quantity_reserved
            
            if self.include_in_transit:
                center_data['quantity_in_transit'] = item.quantity_in_transit
            
            products_dict[sku]['distribution_centers'].append(center_data)
        
        return {
            'products': list(products_dict.values()),
            'total_products': len(products_dict)
        }
