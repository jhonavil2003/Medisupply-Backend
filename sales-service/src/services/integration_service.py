import requests
import os
from src.errors.errors import ExternalServiceError, ValidationError


class IntegrationService:
    """
    Servicio para integrar con microservicios externos (catálogo y logística).
    """
    
    def __init__(self):
        self.catalog_service_url = os.getenv('CATALOG_SERVICE_URL', 'http://localhost:3001')
        self.logistics_service_url = os.getenv('LOGISTICS_SERVICE_URL', 'http://localhost:3002')
        self.timeout = int(os.getenv('EXTERNAL_SERVICE_TIMEOUT', '3'))  # 3 segundos según HU-102
    
    def get_product_by_sku(self, sku):
        """
        Obtiene información del producto desde catalog-service.
        
        Args:
            sku (str): SKU del producto
            
        Returns:
            dict: Información del producto
            
        Raises:
            ExternalServiceError: Si el servicio de catálogo no está disponible
            ValidationError: Si el producto no se encuentra o está inactivo
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
            
            # Validar que el producto esté activo
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
        Verifica disponibilidad de stock en logistics-service.
        
        IMPORTANTE: Usa el endpoint /cart/stock/realtime que considera las reservas
        activas de carrito, evitando sobreventa en escenarios de concurrencia.
        
        Args:
            product_sku (str): SKU del producto
            quantity (int): Cantidad requerida
            distribution_center_code (str, optional): Centro de distribución preferido
            
        Returns:
            dict: Información de stock con estado de disponibilidad
            
        Raises:
            ExternalServiceError: Si el servicio de logística no está disponible
            ValidationError: Si hay stock insuficiente
        """
        try:
            # Usar endpoint de stock en tiempo real que considera reservas de carrito
            url = f"{self.logistics_service_url}/cart/stock/realtime"
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
            
            # Obtener stock real disponible (considerando reservas de carrito)
            total_available = stock_data.get('total_available_for_purchase', 0)
            
            # Verificar si hay suficiente stock
            if total_available < quantity:
                raise ValidationError(
                    f"Insufficient stock for product '{product_sku}'. Required: {quantity}, Available for purchase: {total_available}",
                    payload={
                        'product_sku': product_sku,
                        'required_quantity': quantity,
                        'available_for_purchase': total_available,
                        'physical_stock': stock_data.get('total_physical_stock', 0),
                        'reserved_in_carts': stock_data.get('total_reserved_in_carts', 0),
                        'distribution_centers': stock_data.get('distribution_centers', [])
                    }
                )
            
            # Encontrar el mejor centro de distribución (preferir el que tiene más stock o el especificado)
            distribution_centers = stock_data.get('distribution_centers', [])
            selected_center = None
            
            if distribution_center_code:
                # Intentar usar el centro preferido
                for center in distribution_centers:
                    if center.get('distribution_center_code') == distribution_center_code:
                        # Usar available_for_purchase en lugar de quantity_available
                        if center.get('available_for_purchase', 0) >= quantity:
                            selected_center = center
                            break
            
            if not selected_center and distribution_centers:
                # Seleccionar centro con mayor stock disponible para compra
                distribution_centers_sorted = sorted(
                    distribution_centers,
                    key=lambda x: x.get('available_for_purchase', 0),
                    reverse=True
                )
                for center in distribution_centers_sorted:
                    if center.get('available_for_purchase', 0) >= quantity:
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
        Valida todos los items de la orden (existencia del producto y disponibilidad de stock).
        
        Args:
            items (list): Lista de items de la orden con product_sku y quantity
            preferred_distribution_center (str, optional): Centro de distribución preferido
            
        Returns:
            list: Items validados con información del producto y confirmación de stock
            
        Raises:
            ValidationError: Si algún item es inválido o tiene stock insuficiente
            ExternalServiceError: Si los servicios externos no están disponibles
        """
        validated_items = []
        
        for item in items:
            product_sku = item.get('product_sku')
            quantity = item.get('quantity', 0)
            
            if not product_sku:
                raise ValidationError("Product SKU is required for all items")
            
            if quantity <= 0:
                raise ValidationError(f"Invalid quantity for product '{product_sku}': {quantity}")
            
            # Obtener información del producto desde el catálogo
            product = self.get_product_by_sku(product_sku)
            
            # Verificar disponibilidad de stock
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
