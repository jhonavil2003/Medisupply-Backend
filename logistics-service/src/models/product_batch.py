from src.session import db
from datetime import datetime, date

class ProductBatch(db.Model):
    """
    Modelo para representar lotes específicos de productos almacenados.
    Cada lote tiene información de vencimiento, ubicación y condiciones de almacenamiento.
    """
    __tablename__ = 'product_batches'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Identificación del producto y ubicación
    product_sku = db.Column(db.String(50), nullable=False, index=True)
    distribution_center_id = db.Column(db.Integer, db.ForeignKey('distribution_centers.id'), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('warehouse_locations.id'), nullable=False)
    
    # Información del lote
    batch_number = db.Column(db.String(100), nullable=False, index=True)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    
    # Fechas críticas para rotación FEFO
    expiry_date = db.Column(db.Date, nullable=False, index=True)  # Fecha de vencimiento
    manufactured_date = db.Column(db.Date)  # Fecha de fabricación
    
    # Condiciones de temperatura requeridas para el producto
    required_temperature_min = db.Column(db.Numeric(5, 2))  # Temperatura mínima requerida en °C
    required_temperature_max = db.Column(db.Numeric(5, 2))  # Temperatura máxima requerida en °C
    
    # Códigos de identificación
    barcode = db.Column(db.String(100))  # Código de barras del lote
    qr_code = db.Column(db.String(255))  # Código QR del lote
    
    # Estado del lote
    is_quarantine = db.Column(db.Boolean, default=False)  # Lote en cuarentena
    is_expired = db.Column(db.Boolean, default=False, index=True)  # Lote vencido
    is_available = db.Column(db.Boolean, default=True, index=True)  # Lote disponible para uso
    
    # Información adicional
    notes = db.Column(db.Text)
    internal_code = db.Column(db.String(100))  # Código interno de la organización
    
    # Auditoría
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = db.Column(db.String(100))
    
    # Relaciones
    distribution_center = db.relationship('DistributionCenter', backref='product_batches')
    location = db.relationship('WarehouseLocation', back_populates='product_batches')
    
    # Índices compuestos para búsquedas optimizadas
    __table_args__ = (
        db.UniqueConstraint('product_sku', 'batch_number', 'distribution_center_id', 
                          name='uix_product_batch_dc'),
        db.Index('idx_sku_dc_expiry', 'product_sku', 'distribution_center_id', 'expiry_date'),
        db.Index('idx_location_available', 'location_id', 'is_available'),
        db.Index('idx_expiry_available', 'expiry_date', 'is_available'),
    )
    
    @property
    def days_until_expiry(self):
        """Calcula días hasta el vencimiento"""
        if not self.expiry_date:
            return None
        delta = self.expiry_date - date.today()
        return delta.days
    
    def is_near_expiry(self, days_threshold=30):
        """Indica si el lote está cerca del vencimiento (por defecto 30 días)"""
        days = self.days_until_expiry
        return days is not None and 0 < days <= days_threshold
    
    @property
    def is_expired_check(self):
        """Verifica si el lote está vencido basado en la fecha actual"""
        if not self.expiry_date:
            return False
        return date.today() > self.expiry_date
    
    @property
    def expiry_status(self):
        """Retorna el estado de vencimiento del lote"""
        if self.is_expired_check:
            return 'expired'
        elif self.is_near_expiry(30):
            return 'near_expiry'
        else:
            return 'valid'
    
    @property
    def temperature_range(self):
        """Retorna el rango de temperatura requerido como string"""
        if self.required_temperature_min is None and self.required_temperature_max is None:
            return None
        
        min_temp = f"{float(self.required_temperature_min)}°C" if self.required_temperature_min else "N/A"
        max_temp = f"{float(self.required_temperature_max)}°C" if self.required_temperature_max else "N/A"
        
        return f"{min_temp} - {max_temp}"
    
    def to_dict(self, include_location=True, include_distribution_center=False):
        """Convierte el lote a diccionario"""
        data = {
            'id': self.id,
            'product_sku': self.product_sku,
            'distribution_center_id': self.distribution_center_id,
            'location_id': self.location_id,
            'batch_info': {
                'batch_number': self.batch_number,
                'quantity': self.quantity,
                'internal_code': self.internal_code,
                'barcode': self.barcode,
                'qr_code': self.qr_code,
            },
            'dates': {
                'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
                'manufactured_date': self.manufactured_date.isoformat() if self.manufactured_date else None,
                'days_until_expiry': self.days_until_expiry,
            },
            'temperature_requirements': {
                'min': float(self.required_temperature_min) if self.required_temperature_min else None,
                'max': float(self.required_temperature_max) if self.required_temperature_max else None,
                'range': self.temperature_range,
            },
            'status': {
                'is_available': self.is_available,
                'is_expired': self.is_expired or self.is_expired_check,
                'is_quarantine': self.is_quarantine,
                'is_near_expiry': self.is_near_expiry(),
                'expiry_status': self.expiry_status,
            },
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by,
        }
        
        if include_location and self.location:
            data['location'] = self.location.to_dict()
        
        if include_distribution_center and self.distribution_center:
            data['distribution_center'] = self.distribution_center.to_dict()
        
        return data
    
    def __repr__(self):
        return f'<ProductBatch SKU:{self.product_sku} Batch:{self.batch_number} Qty:{self.quantity} Exp:{self.expiry_date}>'
