import requests
import os
from src.errors.errors import ExternalServiceError, ValidationError


class IntegrationService:
    """
    Service to integrate with external microservices (catalog and logistics).
    """
    
    def __init__(self):
        self.catalog_service_url = os.getenv('CATALOG_SERVICE_URL', 'http://localhost:3001')
        self.logistics_service_url = os.getenv('LOGISTICS_SERVICE_URL', 'http://localhost:3002')
        self.timeout = int(os.getenv('EXTERNAL_SERVICE_TIMEOUT', '3'))  # 3 seconds as per HU-102
    
    def get_product_by_sku(self, sku):
        """
        Get product information from catalog-service.
        
        Args:
            sku (str): Product SKU
            
        Returns:
            dict: Product information
            
        Raises:
            ExternalServiceError: If catalog service is unavailable
            ValidationError: If product is not found or inactive
        """
        try:
            url = f"{self.catalog_service_url}/products/{sku}"
            response = requests.get(url, timeout=self.timeout)
            
            if response.status_code == 404:
                raise ValidationError(f"Product with SKU '{sku}' not found in catalog")
            
            if response.status_code != 200:
                raise ExternalServiceError(
                    f"Catalog service returned status {response.status_code}",
                    payload={'service': 'catalog', 'status_code': response.status_code}
                )
            
            product = response.json()
            
            # Validate product is active
            if not product.get('is_active', False):
                raise ValidationError(
                    f"Product '{sku}' is not active",
                    payload={'sku': sku, 'is_active': False}
                )
            
            return product
            
        except requests.exceptions.Timeout:
            raise ExternalServiceError(
                "Catalog service timeout - request took longer than 3 seconds",
                payload={'service': 'catalog', 'timeout': self.timeout}
            )
        except requests.exceptions.ConnectionError:
            raise ExternalServiceError(
                "Cannot connect to catalog service",
                payload={'service': 'catalog', 'url': self.catalog_service_url}
            )
        except (ValidationError, ExternalServiceError):
            raise
        except Exception as e:
            raise ExternalServiceError(
                f"Unexpected error calling catalog service: {str(e)}",
                payload={'service': 'catalog', 'error': str(e)}
            )
    
    def check_stock_availability(self, product_sku, quantity, distribution_center_code=None):
        """
        Check stock availability in logistics-service.
        
        Args:
            product_sku (str): Product SKU
            quantity (int): Required quantity
            distribution_center_code (str, optional): Preferred distribution center
            
        Returns:
            dict: Stock information with availability status
            
        Raises:
            ExternalServiceError: If logistics service is unavailable
            ValidationError: If insufficient stock
        """
        try:
            url = f"{self.logistics_service_url}/inventory/stock-levels"
            params = {'product_sku': product_sku}
            
            if distribution_center_code:
                params['distribution_center_id'] = distribution_center_code
            
            response = requests.get(url, params=params, timeout=self.timeout)
            
            if response.status_code != 200:
                raise ExternalServiceError(
                    f"Logistics service returned status {response.status_code}",
                    payload={'service': 'logistics', 'status_code': response.status_code}
                )
            
            stock_data = response.json()
            
            # Calculate total available stock
            total_available = stock_data.get('total_available', 0)
            
            # Check if there's enough stock
            if total_available < quantity:
                raise ValidationError(
                    f"Insufficient stock for product '{product_sku}'. Required: {quantity}, Available: {total_available}",
                    payload={
                        'product_sku': product_sku,
                        'required_quantity': quantity,
                        'available_quantity': total_available,
                        'distribution_centers': stock_data.get('distribution_centers', [])
                    }
                )
            
            # Find best distribution center (prefer the one with most stock or specified center)
            distribution_centers = stock_data.get('distribution_centers', [])
            selected_center = None
            
            if distribution_center_code:
                # Try to use preferred center
                for center in distribution_centers:
                    if center.get('distribution_center_code') == distribution_center_code:
                        if center.get('quantity_available', 0) >= quantity:
                            selected_center = center
                            break
            
            if not selected_center and distribution_centers:
                # Select center with most stock
                distribution_centers_sorted = sorted(
                    distribution_centers,
                    key=lambda x: x.get('quantity_available', 0),
                    reverse=True
                )
                for center in distribution_centers_sorted:
                    if center.get('quantity_available', 0) >= quantity:
                        selected_center = center
                        break
            
            return {
                'product_sku': product_sku,
                'required_quantity': quantity,
                'total_available': total_available,
                'stock_confirmed': True,
                'selected_distribution_center': selected_center.get('distribution_center_code') if selected_center else None,
                'distribution_centers': distribution_centers
            }
            
        except requests.exceptions.Timeout:
            raise ExternalServiceError(
                "Logistics service timeout - request took longer than 3 seconds",
                payload={'service': 'logistics', 'timeout': self.timeout}
            )
        except requests.exceptions.ConnectionError:
            raise ExternalServiceError(
                "Cannot connect to logistics service",
                payload={'service': 'logistics', 'url': self.logistics_service_url}
            )
        except (ValidationError, ExternalServiceError):
            raise
        except Exception as e:
            raise ExternalServiceError(
                f"Unexpected error calling logistics service: {str(e)}",
                payload={'service': 'logistics', 'error': str(e)}
            )
    
    def validate_order_items(self, items, preferred_distribution_center=None):
        """
        Validate all order items (product existence and stock availability).
        
        Args:
            items (list): List of order items with product_sku and quantity
            preferred_distribution_center (str, optional): Preferred distribution center
            
        Returns:
            list: Validated items with product info and stock confirmation
            
        Raises:
            ValidationError: If any item is invalid or has insufficient stock
            ExternalServiceError: If external services are unavailable
        """
        validated_items = []
        
        for item in items:
            product_sku = item.get('product_sku')
            quantity = item.get('quantity', 0)
            
            if not product_sku:
                raise ValidationError("Product SKU is required for all items")
            
            if quantity <= 0:
                raise ValidationError(f"Invalid quantity for product '{product_sku}': {quantity}")
            
            # Get product info from catalog
            product = self.get_product_by_sku(product_sku)
            
            # Check stock availability
            stock_info = self.check_stock_availability(
                product_sku,
                quantity,
                preferred_distribution_center
            )
            
            validated_items.append({
                'product_sku': product_sku,
                'product_name': product.get('name'),
                'quantity': quantity,
                'unit_price': product.get('unit_price', 0.0),
                'stock_confirmed': stock_info.get('stock_confirmed', False),
                'distribution_center_code': stock_info.get('selected_distribution_center'),
                'product_data': product,
                'stock_data': stock_info
            })
        
        return validated_items
