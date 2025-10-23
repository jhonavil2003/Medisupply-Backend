from datetime import datetime
from decimal import Decimal
from src.session import db


class OrderItem(db.Model):
    """OrderItem model representing a line item in an order."""
    
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_sku = db.Column(db.String(50), nullable=False, index=True)
    product_name = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(15, 2), nullable=False)
    discount_percentage = db.Column(db.Numeric(5, 2), default=0.0)
    discount_amount = db.Column(db.Numeric(15, 2), default=0.0)
    tax_percentage = db.Column(db.Numeric(5, 2), default=19.0)  # IVA Colombia 19%
    tax_amount = db.Column(db.Numeric(15, 2), default=0.0)
    subtotal = db.Column(db.Numeric(15, 2), nullable=False)
    total = db.Column(db.Numeric(15, 2), nullable=False)
    distribution_center_code = db.Column(db.String(50))  # Centro desde donde se enviará
    stock_confirmed = db.Column(db.Boolean, default=False, nullable=False)
    stock_confirmation_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    order = db.relationship('Order', back_populates='items')
    
    def __repr__(self):
        return f'<OrderItem {self.product_sku}: qty={self.quantity}>'
    
    def to_dict(self):
        """Convert order item to dictionary."""
        return {
            'id': self.id,
            'order_id': self.order_id,
            'product_sku': self.product_sku,
            'product_name': self.product_name,
            'quantity': self.quantity,
            'unit_price': float(self.unit_price) if self.unit_price else 0.0,
            'discount_percentage': float(self.discount_percentage) if self.discount_percentage else 0.0,
            'discount_amount': float(self.discount_amount) if self.discount_amount else 0.0,
            'tax_percentage': float(self.tax_percentage) if self.tax_percentage else 19.0,
            'tax_amount': float(self.tax_amount) if self.tax_amount else 0.0,
            'subtotal': float(self.subtotal) if self.subtotal else 0.0,
            'total': float(self.total) if self.total else 0.0,
            'distribution_center_code': self.distribution_center_code or 'CEDIS-BOG',
            'stock_confirmed': self.stock_confirmed,
            'stock_confirmation_date': self.stock_confirmation_date.isoformat() if self.stock_confirmation_date else '',
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def calculate_totals(self):
        """Calculate discount, tax, and total amounts."""
        # Ensure all values are Decimal for consistent calculations
        unit_price = Decimal(str(self.unit_price)) if not isinstance(self.unit_price, Decimal) else self.unit_price
        quantity = Decimal(str(self.quantity)) if not isinstance(self.quantity, Decimal) else self.quantity
        discount_pct = Decimal(str(self.discount_percentage)) if not isinstance(self.discount_percentage, Decimal) else self.discount_percentage
        tax_pct = Decimal(str(self.tax_percentage)) if not isinstance(self.tax_percentage, Decimal) else self.tax_percentage
        
        # Calculate discount amount
        if discount_pct and discount_pct > 0:
            self.discount_amount = (unit_price * quantity * discount_pct) / Decimal('100')
        else:
            self.discount_amount = Decimal('0.0')
        
        # Calculate subtotal after discount
        self.subtotal = (unit_price * quantity) - self.discount_amount
        
        # Calculate tax amount
        if tax_pct and tax_pct > 0:
            self.tax_amount = (self.subtotal * tax_pct) / Decimal('100')
        else:
            self.tax_amount = Decimal('0.0')
        
        # Calculate total
        self.total = self.subtotal + self.tax_amount
