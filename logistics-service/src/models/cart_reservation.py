"""
Modelo de reservas temporales de carrito.

Este modelo permite reservar stock temporalmente cuando un usuario
agrega productos a su carrito, asegurando que:
- El stock se refleje inmediatamente para todos los usuarios
- Las reservas expiren automáticamente después de 15 minutos
- Se eviten condiciones de carrera en ventas concurrentes
"""

from datetime import datetime, timedelta
from src.session import db


class CartReservation(db.Model):
    """
    Modelo para reservas temporales de stock en carritos de compra.
    
    Cada reserva tiene un TTL (Time To Live) de 15 minutos por defecto.
    Cuando expira, el stock se libera automáticamente.
    """
    __tablename__ = 'cart_reservations'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Identificación del producto
    product_sku = db.Column(db.String(50), nullable=False, index=True)
    
    # Centro de distribución
    distribution_center_id = db.Column(db.Integer, db.ForeignKey('distribution_centers.id'), nullable=False)
    
    # Identificación del usuario y sesión
    user_id = db.Column(db.String(100), nullable=False, index=True)
    session_id = db.Column(db.String(255), nullable=False)
    
    # Cantidad reservada
    quantity_reserved = db.Column(db.Integer, nullable=False)
    
    # Control de tiempo
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False, index=True)
    
    # Estado de la reserva
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)
    
    # Timestamps
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Constraint único: Un usuario/sesión solo puede tener una reserva activa por producto/centro
    __table_args__ = (
        db.UniqueConstraint('user_id', 'session_id', 'product_sku', 'distribution_center_id', name='uq_user_session_product_dc'),
        db.CheckConstraint('quantity_reserved > 0', name='chk_quantity_positive'),
        db.Index('idx_active_reservations', 'product_sku', 'is_active'),
        db.Index('idx_expires_active', 'expires_at', 'is_active'),
        db.Index('idx_cart_reservations_dc', 'distribution_center_id')
    )
    
    @staticmethod
    def get_default_expiration(minutes=15):
        """Calcula la fecha de expiración por defecto (15 minutos desde ahora)."""
        return datetime.utcnow() + timedelta(minutes=minutes)
    
    @property
    def is_expired(self):
        """Verifica si la reserva ha expirado."""
        return datetime.utcnow() >= self.expires_at
    
    @property
    def remaining_time_seconds(self):
        """Calcula el tiempo restante en segundos antes de expirar."""
        if self.is_expired:
            return 0
        delta = self.expires_at - datetime.utcnow()
        return max(0, int(delta.total_seconds()))
    
    def to_dict(self):
        """Convierte la reserva a diccionario."""
        return {
            'id': self.id,
            'product_sku': self.product_sku,
            'distribution_center_id': self.distribution_center_id,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'quantity_reserved': self.quantity_reserved,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_active': self.is_active,
            'is_expired': self.is_expired,
            'remaining_time_seconds': self.remaining_time_seconds,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return (f'<CartReservation {self.id} SKU:{self.product_sku} '
                f'User:{self.user_id} Qty:{self.quantity_reserved} '
                f'Active:{self.is_active}>')
