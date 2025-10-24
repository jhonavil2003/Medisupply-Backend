from src.session import db
from src.models.product_batch import ProductBatch
from src.models.warehouse_location import WarehouseLocation
from src.models.distribution_center import DistributionCenter
from src.errors.errors import NotFoundError, ValidationError
from datetime import date, datetime
from sqlalchemy import or_, and_


class GetProductLocation:
    """
    Comando para consultar la localización de productos en bodega.
    
    Permite búsqueda por:
    - SKU del producto
    - Código de barras
    - Código QR
    - Código interno
    
    Soporta filtros por:
    - Lote específico
    - Rango de fechas de vencimiento
    - Zona/cámara (refrigerado/ambiente)
    - Centro de distribución
    
    Los resultados se ordenan por FEFO (First-Expire-First-Out) por defecto.
    """
    
    def __init__(
        self,
        search_term=None,
        product_sku=None,
        barcode=None,
        qr_code=None,
        internal_code=None,
        distribution_center_id=None,
        batch_number=None,
        zone_type=None,
        expiry_date_from=None,
        expiry_date_to=None,
        include_expired=False,
        include_quarantine=False,
        only_available=True,
        order_by='fefo'
    ):
        """
        Inicializa el comando de búsqueda de localización de productos.
        
        Args:
            search_term: Término de búsqueda general (busca en SKU, barcode, QR, internal_code)
            product_sku: SKU específico del producto
            barcode: Código de barras
            qr_code: Código QR
            internal_code: Código interno
            distribution_center_id: ID del centro de distribución
            batch_number: Número de lote específico
            zone_type: Tipo de zona ('refrigerated' o 'ambient')
            expiry_date_from: Fecha de vencimiento desde (formato YYYY-MM-DD)
            expiry_date_to: Fecha de vencimiento hasta (formato YYYY-MM-DD)
            include_expired: Incluir lotes vencidos
            include_quarantine: Incluir lotes en cuarentena
            only_available: Solo lotes disponibles
            order_by: Criterio de ordenamiento ('fefo', 'quantity', 'location')
        """
        self.search_term = search_term
        self.product_sku = product_sku
        self.barcode = barcode
        self.qr_code = qr_code
        self.internal_code = internal_code
        self.distribution_center_id = distribution_center_id
        self.batch_number = batch_number
        self.zone_type = zone_type
        self.expiry_date_from = expiry_date_from
        self.expiry_date_to = expiry_date_to
        self.include_expired = include_expired
        self.include_quarantine = include_quarantine
        self.only_available = only_available
        self.order_by = order_by
    
    def execute(self):
        """
        Ejecuta la búsqueda de localización de productos.
        
        Returns:
            dict: Diccionario con resultados de búsqueda
            
        Raises:
            ValidationError: Si los parámetros son inválidos
            NotFoundError: Si no se encuentra el producto
        """
        self._validate_parameters()
        
        # Construir query base
        query = db.session.query(ProductBatch).join(
            WarehouseLocation, ProductBatch.location_id == WarehouseLocation.id
        ).join(
            DistributionCenter, ProductBatch.distribution_center_id == DistributionCenter.id
        )
        
        # Aplicar filtros de búsqueda
        query = self._apply_search_filters(query)
        
        # Aplicar filtros adicionales
        query = self._apply_additional_filters(query)
        
        # Aplicar ordenamiento
        query = self._apply_ordering(query)
        
        # Ejecutar query
        batches = query.all()
        
        if not batches:
            # Verificar si el producto existe pero sin stock
            return self._handle_no_results()
        
        # Formatear resultados
        return self._format_results(batches)
    
    def _validate_parameters(self):
        """Valida los parámetros de entrada"""
        if not any([self.search_term, self.product_sku, self.barcode, self.qr_code, self.internal_code]):
            raise ValidationError(
                "Se requiere al menos un parámetro de búsqueda: "
                "search_term, product_sku, barcode, qr_code o internal_code"
            )
        
        if self.zone_type and self.zone_type not in ['refrigerated', 'ambient']:
            raise ValidationError("zone_type debe ser 'refrigerated' o 'ambient'")
        
        if self.order_by and self.order_by not in ['fefo', 'quantity', 'location']:
            raise ValidationError("order_by debe ser 'fefo', 'quantity' o 'location'")
        
        # Validar formato de fechas
        if self.expiry_date_from:
            try:
                datetime.strptime(self.expiry_date_from, '%Y-%m-%d')
            except ValueError:
                raise ValidationError("expiry_date_from debe tener formato YYYY-MM-DD")
        
        if self.expiry_date_to:
            try:
                datetime.strptime(self.expiry_date_to, '%Y-%m-%d')
            except ValueError:
                raise ValidationError("expiry_date_to debe tener formato YYYY-MM-DD")
    
    def _apply_search_filters(self, query):
        """Aplica filtros de búsqueda principal"""
        search_conditions = []
        
        if self.search_term:
            # Búsqueda amplia en múltiples campos
            search_conditions.append(ProductBatch.product_sku.ilike(f'%{self.search_term}%'))
            search_conditions.append(ProductBatch.barcode.ilike(f'%{self.search_term}%'))
            search_conditions.append(ProductBatch.qr_code.ilike(f'%{self.search_term}%'))
            search_conditions.append(ProductBatch.internal_code.ilike(f'%{self.search_term}%'))
            query = query.filter(or_(*search_conditions))
        else:
            # Búsqueda específica por campo
            if self.product_sku:
                query = query.filter(ProductBatch.product_sku == self.product_sku)
            
            if self.barcode:
                query = query.filter(ProductBatch.barcode == self.barcode)
            
            if self.qr_code:
                query = query.filter(ProductBatch.qr_code == self.qr_code)
            
            if self.internal_code:
                query = query.filter(ProductBatch.internal_code == self.internal_code)
        
        return query
    
    def _apply_additional_filters(self, query):
        """Aplica filtros adicionales"""
        # Filtro por centro de distribución
        if self.distribution_center_id:
            query = query.filter(ProductBatch.distribution_center_id == self.distribution_center_id)
        
        # Filtro por número de lote
        if self.batch_number:
            query = query.filter(ProductBatch.batch_number == self.batch_number)
        
        # Filtro por tipo de zona
        if self.zone_type:
            query = query.filter(WarehouseLocation.zone_type == self.zone_type)
        
        # Filtro por rango de fechas de vencimiento
        if self.expiry_date_from:
            expiry_from = datetime.strptime(self.expiry_date_from, '%Y-%m-%d').date()
            query = query.filter(ProductBatch.expiry_date >= expiry_from)
        
        if self.expiry_date_to:
            expiry_to = datetime.strptime(self.expiry_date_to, '%Y-%m-%d').date()
            query = query.filter(ProductBatch.expiry_date <= expiry_to)
        
        # Filtro por estado de vencimiento
        if not self.include_expired:
            query = query.filter(
                and_(
                    ProductBatch.is_expired == False,
                    ProductBatch.expiry_date >= date.today()
                )
            )
        
        # Filtro por cuarentena
        if not self.include_quarantine:
            query = query.filter(ProductBatch.is_quarantine == False)
        
        # Filtro por disponibilidad
        if self.only_available:
            query = query.filter(
                and_(
                    ProductBatch.is_available == True,
                    ProductBatch.quantity > 0
                )
            )
        
        return query
    
    def _apply_ordering(self, query):
        """Aplica ordenamiento a los resultados"""
        if self.order_by == 'fefo':
            # FEFO: First-Expire-First-Out (priorizar lotes que vencen primero)
            query = query.order_by(ProductBatch.expiry_date.asc(), ProductBatch.quantity.desc())
        elif self.order_by == 'quantity':
            query = query.order_by(ProductBatch.quantity.desc(), ProductBatch.expiry_date.asc())
        elif self.order_by == 'location':
            query = query.order_by(
                WarehouseLocation.aisle,
                WarehouseLocation.shelf,
                WarehouseLocation.level_position,
                ProductBatch.expiry_date.asc()
            )
        
        return query
    
    def _handle_no_results(self):
        """Maneja el caso cuando no se encuentran resultados"""
        # Intentar determinar si el producto existe pero sin stock
        search_sku = self.product_sku or self.search_term
        
        if search_sku:
            # Buscar cualquier lote histórico del producto
            historical_batch = db.session.query(ProductBatch).filter(
                ProductBatch.product_sku == search_sku
            ).first()
            
            if historical_batch:
                return {
                    'found': False,
                    'message': 'Producto encontrado pero sin stock en bodega',
                    'product_sku': search_sku,
                    'locations': [],
                    'total_quantity': 0,
                    'has_historical_data': True,
                    'search_criteria': self._get_search_criteria()
                }
        
        raise NotFoundError("Producto no encontrado")
    
    def _format_results(self, batches):
        """Formatea los resultados de búsqueda"""
        locations = []
        total_quantity = 0
        product_skus = set()
        
        for batch in batches:
            product_skus.add(batch.product_sku)
            total_quantity += batch.quantity
            
            location_data = {
                'batch': batch.to_dict(include_location=False),
                'physical_location': {
                    'aisle': batch.location.aisle,
                    'shelf': batch.location.shelf,
                    'level_position': batch.location.level_position,
                    'location_code': batch.location.location_code,
                    'zone_type': batch.location.zone_type,
                    'is_refrigerated': batch.location.is_refrigerated,
                },
                'distribution_center': {
                    'id': batch.distribution_center.id,
                    'code': batch.distribution_center.code,
                    'name': batch.distribution_center.name,
                    'city': batch.distribution_center.city,
                    'supports_cold_chain': batch.distribution_center.supports_cold_chain,
                },
            }
            
            # Agregar información de temperatura si es zona refrigerada
            if batch.location.is_refrigerated:
                location_data['temperature_status'] = {
                    'required_range': batch.temperature_range,
                    'current': float(batch.location.current_temperature) if batch.location.current_temperature else None,
                    'min_allowed': float(batch.location.temperature_min) if batch.location.temperature_min else None,
                    'max_allowed': float(batch.location.temperature_max) if batch.location.temperature_max else None,
                    'in_range': batch.location.temperature_in_range,
                }
            
            locations.append(location_data)
        
        return {
            'found': True,
            'product_skus': list(product_skus),
            'total_locations': len(locations),
            'total_quantity': total_quantity,
            'locations': locations,
            'ordering': self.order_by,
            'search_criteria': self._get_search_criteria(),
            'timestamp': datetime.utcnow().isoformat(),
        }
    
    def _get_search_criteria(self):
        """Retorna los criterios de búsqueda utilizados"""
        return {
            'search_term': self.search_term,
            'product_sku': self.product_sku,
            'barcode': self.barcode,
            'qr_code': self.qr_code,
            'internal_code': self.internal_code,
            'distribution_center_id': self.distribution_center_id,
            'batch_number': self.batch_number,
            'zone_type': self.zone_type,
            'expiry_date_from': self.expiry_date_from,
            'expiry_date_to': self.expiry_date_to,
            'include_expired': self.include_expired,
            'include_quarantine': self.include_quarantine,
            'only_available': self.only_available,
        }
