from datetime import datetime
from decimal import Decimal
import requests
import os
import logging
from src.models.order import Order
from src.models.order_item import OrderItem
from src.models.customer import Customer
from src.session import db
from src.errors.errors import ValidationError, NotFoundError
from src.services.integration_service import IntegrationService

logger = logging.getLogger(__name__)


class CreateOrder:
    """Command to create a new order with real-time stock validation."""
    
    def __init__(self, data):
        self.data = data
        self.integration_service = IntegrationService()
    
    def execute(self):
        """
        Execute the command to create an order.
        
        Returns:
            dict: Created order dictionary
            
        Raises:
            ValidationError: If validation fails
            NotFoundError: If customer not found
        """

        self._validate_required_fields()
        
        customer = self._validate_customer()
        
        validated_items = self._validate_items()
        
        order_totals = self._calculate_order_totals(validated_items)
        
        order = self._create_order(customer, order_totals)
        
        self._create_order_items(order, validated_items)
        
        db.session.commit()
        
        # Limpiar reservas de carrito después de confirmar la orden
        self._clear_cart_reservations()
        
        return order.to_dict(include_items=True, include_customer=True)
    
    def _validate_required_fields(self):
        """Validate required fields in the request."""
        required_fields = ['customer_id', 'seller_id', 'items']
        
        for field in required_fields:
            if field not in self.data or not self.data[field]:
                raise ValidationError(f"Field '{field}' is required")
        
        if not isinstance(self.data['items'], list) or len(self.data['items']) == 0:
            raise ValidationError("Order must have at least one item")
    
    def _validate_customer(self):
        """Validate customer exists and is active."""
        customer_id = self.data['customer_id']
        customer = Customer.query.filter_by(id=customer_id).first()
        
        if not customer:
            raise NotFoundError(f"Customer with ID {customer_id} not found")
        
        if not customer.is_active:
            raise ValidationError(f"Customer {customer.business_name} is not active")
        
        return customer
    
    def _validate_items(self):
        """Validate all order items (product existence and stock availability)."""
        items = self.data['items']
        preferred_distribution_center = self.data.get('preferred_distribution_center')
        
        validated_items = self.integration_service.validate_order_items(
            items,
            preferred_distribution_center
        )
        
        for i, item in enumerate(items):
            validated_items[i]['discount_percentage'] = item.get('discount_percentage', 0.0)
            validated_items[i]['tax_percentage'] = item.get('tax_percentage', 19.0)
        
        return validated_items
    
    def _calculate_order_totals(self, validated_items):
        """Calculate order totals (subtotal, discount, tax, total)."""
        subtotal = Decimal('0.0')
        total_discount = Decimal('0.0')
        total_tax = Decimal('0.0')
        
        for item in validated_items:
            quantity = Decimal(str(item['quantity']))
            unit_price = Decimal(str(item['unit_price']))
            discount_percentage = Decimal(str(item.get('discount_percentage', 0.0)))
            tax_percentage = Decimal(str(item.get('tax_percentage', 19.0)))
            
            item_subtotal = unit_price * quantity
            
            item_discount = (item_subtotal * discount_percentage) / Decimal('100')
            total_discount += item_discount
            
            item_subtotal_after_discount = item_subtotal - item_discount
            subtotal += item_subtotal_after_discount
            
            item_tax = (item_subtotal_after_discount * tax_percentage) / Decimal('100')
            total_tax += item_tax
        
        total_amount = subtotal + total_tax
        
        return {
            'subtotal': subtotal,
            'discount_amount': total_discount,
            'tax_amount': total_tax,
            'total_amount': total_amount
        }
    
    def _create_order(self, customer, totals):
        """Create order record."""
        order = Order(
            order_number=self._generate_order_number(),
            customer_id=customer.id,
            # Customer snapshot - datos del cliente al momento de crear la orden
            customer_business_name=customer.business_name,
            customer_document_number=customer.document_number,
            customer_contact_name=customer.contact_name,
            customer_contact_phone=customer.contact_phone,
            customer_contact_email=customer.contact_email,
            # Seller information
            seller_id=self.data['seller_id'],
            seller_name=self.data.get('seller_name'),
            order_date=datetime.utcnow(),
            status='pending',
            subtotal=totals['subtotal'],
            discount_amount=totals['discount_amount'],
            tax_amount=totals['tax_amount'],
            total_amount=totals['total_amount'],
            payment_terms=self.data.get('payment_terms', 'contado'),
            payment_method=self.data.get('payment_method'),
            # Delivery information - usa datos del request o fallback a datos del cliente
            delivery_address=self.data.get('delivery_address', customer.address),
            delivery_neighborhood=self.data.get('delivery_neighborhood', customer.neighborhood),
            delivery_city=self.data.get('delivery_city', customer.city),
            delivery_department=self.data.get('delivery_department', customer.department),
            delivery_latitude=self.data.get('delivery_latitude', customer.latitude),
            delivery_longitude=self.data.get('delivery_longitude', customer.longitude),
            delivery_date=self._parse_delivery_date(self.data.get('delivery_date')),
            preferred_distribution_center=self.data.get('preferred_distribution_center'),
            notes=self.data.get('notes')
        )
        
        db.session.add(order)
        db.session.flush()  # Get order ID
        
        return order
    
    def _create_order_items(self, order, validated_items):
        """Create order item records."""
        for item_data in validated_items:
            # Use item's distribution center or fall back to order's preferred center
            distribution_center = (
                item_data.get('distribution_center_code') or 
                order.preferred_distribution_center or 
                'CEDIS-BOG'  # Default fallback
            )
            
            order_item = OrderItem(
                order_id=order.id,
                product_sku=item_data['product_sku'],
                product_name=item_data['product_name'],
                quantity=item_data['quantity'],
                unit_price=item_data['unit_price'],
                discount_percentage=item_data.get('discount_percentage', 0.0),
                tax_percentage=item_data.get('tax_percentage', 19.0),
                distribution_center_code=distribution_center,
                stock_confirmed=item_data.get('stock_confirmed', False),
                stock_confirmation_date=datetime.utcnow()
            )
            
            # Calculate item totals
            order_item.calculate_totals()
            
            db.session.add(order_item)
    
    def _generate_order_number(self):
        """Generate unique order number."""
        today = datetime.utcnow().strftime('%Y%m%d')
        
        count = Order.query.filter(
            Order.order_number.like(f'ORD-{today}-%')
        ).count()
        
        sequence = str(count + 1).zfill(4)
        return f'ORD-{today}-{sequence}'
    
    def _parse_delivery_date(self, delivery_date_str):
        """Parse delivery date string to datetime object."""
        if not delivery_date_str:
            return None
        
        try:
            # Expect format YYYY-MM-DD or YYYY-MM-DD HH:MM:SS
            if len(delivery_date_str) == 10:  # YYYY-MM-DD
                return datetime.strptime(delivery_date_str, '%Y-%m-%d')
            elif len(delivery_date_str) == 19:  # YYYY-MM-DD HH:MM:SS
                return datetime.strptime(delivery_date_str, '%Y-%m-%d %H:%M:%S')
            else:
                return None
        except ValueError:
            return None
    
    def _clear_cart_reservations(self):
        """
        Limpia las reservas de carrito del usuario después de crear la orden.
        
        Esto evita que el stock quede bloqueado por reservas que ya fueron
        convertidas en una orden confirmada.
        """
        user_id = self.data.get('user_id')
        session_id = self.data.get('session_id')
        
        # Solo limpiar si se proporcionaron user_id y session_id
        if not user_id or not session_id:
            logger.info("No se proporcionó user_id/session_id, omitiendo limpieza de carrito")
            return
        
        try:
            logistics_url = os.getenv('LOGISTICS_SERVICE_URL', 'http://localhost:3002')
            url = f"{logistics_url}/cart/clear"
            
            response = requests.post(
                url,
                json={
                    'user_id': user_id,
                    'session_id': session_id
                },
                timeout=3
            )
            
            if response.status_code == 200:
                result = response.json()
                cleared_count = result.get('cleared_count', 0)
                logger.info(
                    f"✅ Carrito limpiado exitosamente: {cleared_count} reservas liberadas "
                    f"para user_id={user_id}, session_id={session_id}"
                )
            else:
                logger.warning(
                    f"⚠️ No se pudo limpiar carrito (status {response.status_code}): "
                    f"user_id={user_id}, session_id={session_id}"
                )
        
        except requests.exceptions.Timeout:
            logger.warning(
                f"⚠️ Timeout al limpiar carrito para user_id={user_id}. "
                "Las reservas expirarán automáticamente en 15 minutos."
            )
        
        except requests.exceptions.ConnectionError:
            logger.warning(
                f"⚠️ No se pudo conectar al servicio de logística para limpiar carrito. "
                f"user_id={user_id}. Las reservas expirarán automáticamente."
            )
        
        except Exception as e:
            logger.warning(
                f"⚠️ Error inesperado al limpiar carrito: {str(e)}. "
                "Las reservas expirarán automáticamente en 15 minutos."
            )
