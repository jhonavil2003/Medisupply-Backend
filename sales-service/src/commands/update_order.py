"""
Command to update an existing order.

This command handles partial updates (PATCH) for orders.
Only orders in 'pending' status can be updated.
Immutable fields (customer_id, seller_id, order_number, etc.) are protected.
"""
from datetime import datetime
from decimal import Decimal
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from src.session import db
from src.models.order import Order
from src.models.order_item import OrderItem
from src.errors.errors import NotFoundError, ApiError, ValidationError, DatabaseError


class UpdateOrder:
    """
    Updates an existing order with new values (PATCH - partial update).
    
    Allowed updates:
    - status (pending → confirmed, etc.)
    - payment_method
    - payment_terms (CASH, CREDIT_30, CREDIT_45, etc.)
    - delivery_address, delivery_city, delivery_department
    - preferred_distribution_center
    - notes
    - items (complete replacement of order items)
    
    NOT allowed (immutable):
    - customer_id
    - seller_id
    - order_number
    - order_date
    - created_at
    - Monetary totals (auto-calculated)
    
    Business Rules:
    - Only orders in 'pending' status can be updated
    - If items are updated, totals are recalculated automatically
    - Tax percentage defaults to 19% (IVA Colombia)
    """
    
    # Valid order statuses that can be updated
    EDITABLE_STATUSES = ['pending']
    
    # Immutable fields that cannot be changed
    IMMUTABLE_FIELDS = [
        'customer_id', 'seller_id', 'seller_name',
        'order_number', 'order_date', 'created_at',
        'subtotal', 'discount_amount', 'tax_amount', 'total_amount'
    ]
    
    # Fields that can be updated
    UPDATABLE_FIELDS = [
        'status', 'payment_method', 'payment_terms',
        'delivery_address', 'delivery_city', 'delivery_department',
        'preferred_distribution_center', 'notes'
    ]
    
    def __init__(self, order_id: int, order_data: dict):
        """
        Initialize the update command.
        
        Args:
            order_id: ID of the order to update
            order_data: Dictionary with fields to update (partial update)
        """
        self.order_id = order_id
        self.order_data = order_data
    
    def execute(self):
        """
        Execute the order update.
        
        Returns:
            dict: Updated order data with all relationships
            
        Raises:
            NotFoundError: If order doesn't exist (404)
            ValidationError: If validation fails (400)
            ApiError: If business rules are violated (400)
            DatabaseError: If database operation fails (500)
        """
        try:
            # 1. Find the order
            order = Order.query.get(self.order_id)
            if not order:
                raise NotFoundError(f"Order with id {self.order_id} not found")
            
            # 2. Validate order status (only pending orders can be updated)
            if order.status not in self.EDITABLE_STATUSES:
                raise ApiError(
                    "Solo se pueden editar órdenes pendientes",
                    400
                )
            
            # 3. Remove immutable fields silently (don't raise error, just ignore them)
            self._remove_immutable_fields()
            
            # 4. Validate request data format
            self._validate_request_data()
            
            # 5. Update simple fields
            self._update_simple_fields(order)
            
            # 6. Update items if provided (complete replacement)
            items_updated = False
            if 'items' in self.order_data:
                self._update_order_items(order)
                items_updated = True
            
            # 7. Recalculate totals if items were changed
            if items_updated:
                self._recalculate_totals(order)
            
            # 8. Auto-confirm order: Change status from PENDING to CONFIRMED after update
            if order.status == 'pending':
                order.status = 'confirmed'
            
            # 9. Save changes to database
            try:
                db.session.commit()
            except IntegrityError as e:
                db.session.rollback()
                raise DatabaseError(f"Database integrity error: {str(e)}")
            except SQLAlchemyError as e:
                db.session.rollback()
                raise DatabaseError(f"Database error while updating order: {str(e)}")
            
            # 10. Return updated order with all relationships
            return order.to_dict(include_items=True, include_customer=True)
        
        except (NotFoundError, ApiError, ValidationError, DatabaseError):
            # Re-raise known errors
            raise
        except Exception as e:
            # Catch any unexpected errors and convert to 500
            db.session.rollback()
            raise DatabaseError(f"Unexpected error while updating order: {str(e)}")
    
    def _remove_immutable_fields(self):
        """
        Remove immutable fields from order_data silently.
        This prevents accidental modification of protected fields.
        """
        for field in self.IMMUTABLE_FIELDS:
            if field in self.order_data:
                del self.order_data[field]
    
    def _validate_request_data(self):
        """
        Validate request data format before processing.
        
        Raises:
            ValidationError: If data format is invalid (400)
        """
        # Validate that order_data is a dictionary
        if not isinstance(self.order_data, dict):
            raise ValidationError("Request body must be a valid JSON object")
        
        # Validate status field if present
        if 'status' in self.order_data:
            status = self.order_data['status']
            if not isinstance(status, str):
                raise ValidationError("Field 'status' must be a string")
            if status and status not in ['pending', 'confirmed', 'cancelled', 'delivered', 'in_transit']:
                raise ValidationError(f"Invalid status value: '{status}'")
        
        # Validate numeric fields if present
        numeric_fields = ['payment_terms', 'payment_method', 'delivery_address', 
                         'delivery_city', 'delivery_department', 'preferred_distribution_center', 'notes']
        for field in numeric_fields:
            if field in self.order_data and self.order_data[field] is not None:
                if not isinstance(self.order_data[field], str):
                    raise ValidationError(f"Field '{field}' must be a string")
        
        # Validate items format if present
        if 'items' in self.order_data:
            items = self.order_data['items']
            if not isinstance(items, list):
                raise ValidationError("Field 'items' must be a list")
            if len(items) == 0:
                raise ValidationError("Field 'items' cannot be an empty list. Order must have at least one item")
            
            # Validate each item
            for idx, item in enumerate(items):
                if not isinstance(item, dict):
                    raise ValidationError(f"Item at index {idx} must be a valid object")
                
                # Validate required fields
                if 'product_sku' not in item:
                    raise ValidationError(f"Item at index {idx} is missing required field: 'product_sku'")
                if 'quantity' not in item:
                    raise ValidationError(f"Item at index {idx} is missing required field: 'quantity'")
                
                # Validate quantity
                try:
                    qty = int(item['quantity'])
                    if qty <= 0:
                        raise ValidationError(f"Item at index {idx}: quantity must be greater than 0")
                except (ValueError, TypeError):
                    raise ValidationError(f"Item at index {idx}: quantity must be a valid integer")
                
                # Validate numeric fields in items
                if 'unit_price' in item and item['unit_price'] is not None:
                    try:
                        price = float(item['unit_price'])
                        if price < 0:
                            raise ValidationError(f"Item at index {idx}: unit_price cannot be negative")
                    except (ValueError, TypeError):
                        raise ValidationError(f"Item at index {idx}: unit_price must be a valid number")
                
                if 'discount_percentage' in item and item['discount_percentage'] is not None:
                    try:
                        discount = float(item['discount_percentage'])
                        if discount < 0 or discount > 100:
                            raise ValidationError(f"Item at index {idx}: discount_percentage must be between 0 and 100")
                    except (ValueError, TypeError):
                        raise ValidationError(f"Item at index {idx}: discount_percentage must be a valid number")
                
                if 'tax_percentage' in item and item['tax_percentage'] is not None:
                    try:
                        tax = float(item['tax_percentage'])
                        if tax < 0 or tax > 100:
                            raise ValidationError(f"Item at index {idx}: tax_percentage must be between 0 and 100")
                    except (ValueError, TypeError):
                        raise ValidationError(f"Item at index {idx}: tax_percentage must be a valid number")
    
    def _update_simple_fields(self, order: Order):
        """
        Update simple scalar fields (strings, status, etc.).
        
        Args:
            order: Order instance to update
        """
        for field in self.UPDATABLE_FIELDS:
            if field in self.order_data:
                value = self.order_data[field]
                
                # Validate status transitions if updating status
                if field == 'status' and value is not None:
                    self._validate_status_transition(order.status, value)
                
                setattr(order, field, value)
    
    def _validate_status_transition(self, current_status: str, new_status: str):
        """
        Validate that the status transition is allowed.
        
        Valid transitions from 'pending':
        - pending → confirmed
        - pending → pending (no change)
        
        Args:
            current_status: Current order status
            new_status: Requested new status
            
        Raises:
            ApiError: If transition is not allowed
        """
        valid_transitions = {
            'pending': ['confirmed', 'pending']
        }
        
        allowed = valid_transitions.get(current_status, [])
        if new_status not in allowed:
            raise ApiError(
                f"Invalid status transition: '{current_status}' → '{new_status}'. "
                f"Allowed transitions: {', '.join(allowed)}",
                400
            )
    
    def _update_order_items(self, order: Order):
        """
        Replace all order items with new ones.
        This is a complete replacement, not a merge.
        
        Args:
            order: Order instance to update
            
        Raises:
            ValidationError: If items data is invalid (400)
        """
        items_data = self.order_data.get('items', [])
        
        if not isinstance(items_data, list):
            raise ValidationError("Field 'items' must be a list")
        
        if len(items_data) == 0:
            raise ValidationError("Order must have at least one item")
        
        # Delete all existing items
        try:
            OrderItem.query.filter_by(order_id=order.id).delete()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error deleting existing items: {str(e)}")
        
        # Create new items
        for idx, item_data in enumerate(items_data):
            try:
                self._validate_item_data(item_data, idx)
                
                item = OrderItem(
                    order_id=order.id,
                    product_sku=item_data['product_sku'],
                    product_name=item_data.get('product_name', ''),
                    quantity=item_data['quantity'],
                    unit_price=Decimal(str(item_data['unit_price'])),
                    discount_percentage=Decimal(str(item_data.get('discount_percentage', 0.0))),
                    tax_percentage=Decimal(str(item_data.get('tax_percentage', 19.0))),
                    distribution_center_code=item_data.get(
                        'distribution_center_code',
                        order.preferred_distribution_center or 'CEDIS-BOG'
                    ),
                    stock_confirmed=item_data.get('stock_confirmed', False),
                    stock_confirmation_date=datetime.utcnow()
                )
                
                # Calculate item totals
                item.calculate_totals()
                
                db.session.add(item)
            except (ValueError, TypeError) as e:
                raise ValidationError(f"Invalid data format for item at index {idx}: {str(e)}")
            except SQLAlchemyError as e:
                raise DatabaseError(f"Error creating item at index {idx}: {str(e)}")
    
    def _validate_item_data(self, item_data: dict, idx: int = 0):
        """
        Validate that item data has required fields and valid values.
        
        Args:
            item_data: Dictionary with item data
            idx: Index of the item in the list (for error messages)
            
        Raises:
            ValidationError: If required fields are missing or invalid (400)
        """
        # Validate required fields
        required_fields = ['product_sku', 'quantity', 'unit_price']
        for field in required_fields:
            if field not in item_data:
                raise ValidationError(f"Item at index {idx} is missing required field: '{field}'")
        
        # Validate quantity
        try:
            quantity = int(item_data['quantity'])
            if quantity <= 0:
                raise ValidationError(f"Item at index {idx}: quantity must be greater than 0 (received: {quantity})")
        except (ValueError, TypeError):
            raise ValidationError(f"Item at index {idx}: quantity must be a valid positive integer")
        
        # Validate unit_price
        try:
            unit_price = float(item_data['unit_price'])
            if unit_price < 0:
                raise ValidationError(f"Item at index {idx}: unit_price cannot be negative (received: {unit_price})")
        except (ValueError, TypeError):
            raise ValidationError(f"Item at index {idx}: unit_price must be a valid number")
        
        # Validate product_sku is not empty
        if not item_data['product_sku'] or not str(item_data['product_sku']).strip():
            raise ValidationError(f"Item at index {idx}: product_sku cannot be empty")
    
    def _recalculate_totals(self, order: Order):
        """
        Recalculate order totals based on items.
        
        This method:
        1. Sums up all item subtotals
        2. Sums up all item discounts
        3. Sums up all item taxes
        4. Calculates total amount
        
        Args:
            order: Order instance to recalculate
        """
        # Get all items for this order
        items = list(order.items)
        
        if not items:
            # If no items, set all totals to 0
            order.subtotal = Decimal('0.00')
            order.discount_amount = Decimal('0.00')
            order.tax_amount = Decimal('0.00')
            order.total_amount = Decimal('0.00')
            return
        
        # Calculate totals from items
        subtotal = Decimal('0.00')
        discount_amount = Decimal('0.00')
        tax_amount = Decimal('0.00')
        
        for item in items:
            # Item subtotal before discount and tax
            item_subtotal_before = Decimal(str(item.quantity)) * item.unit_price
            
            # Item discount
            item_discount = item_subtotal_before * (item.discount_percentage / Decimal('100.0'))
            
            # Item subtotal after discount
            item_subtotal_after = item_subtotal_before - item_discount
            
            # Item tax
            item_tax = item_subtotal_after * (item.tax_percentage / Decimal('100.0'))
            
            # Accumulate
            subtotal += item_subtotal_before
            discount_amount += item_discount
            tax_amount += item_tax
        
        # Calculate total
        total_amount = subtotal - discount_amount + tax_amount
        
        # Update order totals (rounded to 2 decimals)
        order.subtotal = round(subtotal, 2)
        order.discount_amount = round(discount_amount, 2)
        order.tax_amount = round(tax_amount, 2)
        order.total_amount = round(total_amount, 2)
