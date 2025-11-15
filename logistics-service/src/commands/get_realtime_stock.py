"""
Comando para obtener stock disponible en tiempo real considerando reservas de carrito
"""
from src.models.inventory import Inventory
from src.models.cart_reservation import CartReservation
from src.models.distribution_center import DistributionCenter
from src.session import db
from sqlalchemy import and_, func
from datetime import datetime


class GetRealTimeStock:
    """
    Obtiene el stock disponible en tiempo real considerando:
    - Stock físico disponible (inventory.quantity_available)
    - Reservas activas de carrito (cart_reservations no expiradas)
    
    El stock real disponible = quantity_available - SUM(cart_reservations activas)
    """
    
    def __init__(self, product_sku=None, product_skus=None, distribution_center_id=None):
        self.product_sku = product_sku
        self.product_skus = product_skus or []
        self.distribution_center_id = distribution_center_id
    
    def execute(self):
        """
        Ejecuta la consulta y retorna el stock disponible en tiempo real
        """
        # Construir query base
        query = db.session.query(
            Inventory.product_sku,
            Inventory.distribution_center_id,
            Inventory.quantity_available,
            func.coalesce(
                func.sum(CartReservation.quantity_reserved).filter(
                    and_(
                        CartReservation.product_sku == Inventory.product_sku,
                        CartReservation.distribution_center_id == Inventory.distribution_center_id,
                        CartReservation.expires_at > datetime.utcnow()
                    )
                ),
                0
            ).label('quantity_reserved_in_cart'),
            DistributionCenter.code,
            DistributionCenter.name,
            DistributionCenter.city
        ).join(
            DistributionCenter,
            Inventory.distribution_center_id == DistributionCenter.id
        ).outerjoin(
            CartReservation,
            and_(
                CartReservation.product_sku == Inventory.product_sku,
                CartReservation.distribution_center_id == Inventory.distribution_center_id,
                CartReservation.expires_at > datetime.utcnow()
            )
        )
        
        # Aplicar filtros
        filters = [DistributionCenter.is_active == True]
        
        if self.product_sku:
            filters.append(Inventory.product_sku == self.product_sku.upper())
        
        if self.product_skus:
            skus_upper = [sku.upper() for sku in self.product_skus]
            filters.append(Inventory.product_sku.in_(skus_upper))
        
        if self.distribution_center_id:
            filters.append(Inventory.distribution_center_id == self.distribution_center_id)
        
        query = query.filter(and_(*filters))
        query = query.group_by(
            Inventory.product_sku,
            Inventory.distribution_center_id,
            Inventory.quantity_available,
            DistributionCenter.code,
            DistributionCenter.name,
            DistributionCenter.city
        )
        
        results = query.all()
        
        if self.product_sku or (self.product_skus and len(self.product_skus) == 1):
            return self._format_single_product_response(results)
        else:
            return self._format_multiple_products_response(results)
    
    def _format_single_product_response(self, results):
        """
        Formatea respuesta para consulta de un solo producto
        """
        if not results:
            return {
                'product_sku': self.product_sku or (self.product_skus[0] if self.product_skus else None),
                'total_physical_stock': 0,
                'total_reserved_in_carts': 0,
                'total_available_for_purchase': 0,
                'distribution_centers': []
            }
        
        product_sku = results[0][0]
        total_physical = sum(r[2] for r in results)
        total_reserved = sum(r[3] for r in results)
        
        centers = []
        for result in results:
            (sku, dc_id, qty_available, qty_reserved, dc_code, dc_name, dc_city) = result
            available_for_purchase = max(0, qty_available - qty_reserved)
            
            centers.append({
                'distribution_center_id': dc_id,
                'distribution_center_code': dc_code,
                'distribution_center_name': dc_name,
                'city': dc_city,
                'physical_stock': qty_available,
                'reserved_in_carts': int(qty_reserved),
                'available_for_purchase': available_for_purchase,
                'is_out_of_stock': available_for_purchase == 0
            })
        
        return {
            'product_sku': product_sku,
            'total_physical_stock': total_physical,
            'total_reserved_in_carts': int(total_reserved),
            'total_available_for_purchase': max(0, total_physical - total_reserved),
            'distribution_centers': centers
        }
    
    def _format_multiple_products_response(self, results):
        """
        Formatea respuesta para consulta de múltiples productos
        """
        products_dict = {}
        
        for result in results:
            (sku, dc_id, qty_available, qty_reserved, dc_code, dc_name, dc_city) = result
            
            if sku not in products_dict:
                products_dict[sku] = {
                    'product_sku': sku,
                    'total_physical_stock': 0,
                    'total_reserved_in_carts': 0,
                    'total_available_for_purchase': 0,
                    'distribution_centers': []
                }
            
            available_for_purchase = max(0, qty_available - qty_reserved)
            
            products_dict[sku]['total_physical_stock'] += qty_available
            products_dict[sku]['total_reserved_in_carts'] += int(qty_reserved)
            products_dict[sku]['total_available_for_purchase'] += available_for_purchase
            
            products_dict[sku]['distribution_centers'].append({
                'distribution_center_id': dc_id,
                'distribution_center_code': dc_code,
                'distribution_center_name': dc_name,
                'city': dc_city,
                'physical_stock': qty_available,
                'reserved_in_carts': int(qty_reserved),
                'available_for_purchase': available_for_purchase,
                'is_out_of_stock': available_for_purchase == 0
            })
        
        return {
            'products': list(products_dict.values()),
            'total_products': len(products_dict)
        }
