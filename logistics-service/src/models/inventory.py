from src.session import db
from datetime import datetime
from decimal import Decimal

class Inventory(db.Model):
    __tablename__ = 'inventory'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    product_sku = db.Column(db.String(50), nullable=False, index=True)
    distribution_center_id = db.Column(db.Integer, db.ForeignKey('distribution_centers.id'), nullable=False)
    
    quantity_available = db.Column(db.Integer, nullable=False, default=0)
    quantity_reserved = db.Column(db.Integer, nullable=False, default=0)
    quantity_in_transit = db.Column(db.Integer, nullable=False, default=0)
    
    minimum_stock_level = db.Column(db.Integer, default=0)
    maximum_stock_level = db.Column(db.Integer)
    reorder_point = db.Column(db.Integer)
    
    unit_cost = db.Column(db.Numeric(10, 2))
    
    last_restock_date = db.Column(db.DateTime)
    last_movement_date = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    distribution_center = db.relationship('DistributionCenter', back_populates='inventory_items')
    
    __table_args__ = (
        db.UniqueConstraint('product_sku', 'distribution_center_id', name='uix_product_center'),
        db.Index('idx_product_center', 'product_sku', 'distribution_center_id'),
    )
    
    @property
    def quantity_total(self):
        return self.quantity_available + self.quantity_reserved + self.quantity_in_transit
    
    @property
    def is_low_stock(self):
        return self.quantity_available <= self.minimum_stock_level
    
    @property
    def is_out_of_stock(self):
        return self.quantity_available == 0
    
    def to_dict(self, include_center=False):
        data = {
            'id': self.id,
            'product_sku': self.product_sku,
            'distribution_center_id': self.distribution_center_id,
            'quantity_available': self.quantity_available,
            'quantity_reserved': self.quantity_reserved,
            'quantity_in_transit': self.quantity_in_transit,
            'quantity_total': self.quantity_total,
            'minimum_stock_level': self.minimum_stock_level,
            'maximum_stock_level': self.maximum_stock_level,
            'reorder_point': self.reorder_point,
            'unit_cost': float(self.unit_cost) if self.unit_cost else None,
            'is_low_stock': self.is_low_stock,
            'is_out_of_stock': self.is_out_of_stock,
            'last_restock_date': self.last_restock_date.isoformat() if self.last_restock_date else None,
            'last_movement_date': self.last_movement_date.isoformat() if self.last_movement_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if include_center and self.distribution_center:
            data['distribution_center'] = self.distribution_center.to_dict()
        
        return data
    
    def update_quantity_available(self, new_quantity: int, auto_notify: bool = True):
        """
        Actualiza quantity_available y dispara evento de WebSocket si hay cambio significativo.
        
        Args:
            new_quantity: Nueva cantidad disponible
            auto_notify: Si True, notifica automáticamente el cambio vía WebSocket
        """
        from src.websockets.inventory_events import track_inventory_change
        
        previous_quantity = self.quantity_available
        self.quantity_available = new_quantity
        self.last_movement_date = datetime.utcnow()
        
        if auto_notify:
            # Rastrear y notificar el cambio
            track_inventory_change(
                product_sku=self.product_sku,
                previous_quantity=previous_quantity,
                new_quantity=new_quantity,
                distribution_center_id=self.distribution_center_id,
                distribution_center_code=self.distribution_center.code if self.distribution_center else None,
                minimum_stock_level=self.minimum_stock_level,
                reorder_point=self.reorder_point,
                metadata={
                    'inventory_id': self.id,
                    'quantity_reserved': self.quantity_reserved,
                    'quantity_in_transit': self.quantity_in_transit
                },
                auto_publish=True
            )
    
    def __repr__(self):
        return f'<Inventory SKU:{self.product_sku} DC:{self.distribution_center_id} Qty:{self.quantity_available}>'
