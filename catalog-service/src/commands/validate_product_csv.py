"""
Comando para validar archivos CSV de carga masiva de productos.
Valida estructura, tipos de datos y reglas de negocio.
"""
import csv
import io
from typing import Dict, List, Tuple, Optional
from decimal import Decimal, InvalidOperation
from src.models.product import Product
from src.models.supplier import Supplier
from src.session import db


class CSVValidationError(Exception):
    """Excepción personalizada para errores de validación de CSV"""
    pass


class ValidateProductCSV:
    """
    Comando para validar archivos CSV de productos.
    Realiza validaciones de estructura y contenido en dos fases.
    """
    
    # Columnas requeridas en el CSV
    REQUIRED_COLUMNS = [
        'sku', 'name', 'category', 'unit_price', 'currency', 
        'unit_of_measure', 'supplier_id'
    ]
    
    # Columnas opcionales permitidas
    OPTIONAL_COLUMNS = [
        'description', 'subcategory', 'requires_cold_chain', 
        'storage_temperature_min', 'storage_temperature_max', 'storage_humidity_max',
        'sanitary_registration', 'requires_prescription', 'regulatory_class',
        'weight_kg', 'length_cm', 'width_cm', 'height_cm',
        'manufacturer', 'country_of_origin', 'barcode', 'image_url',
        'is_active', 'is_discontinued'
    ]
    
    # Categorías válidas
    VALID_CATEGORIES = ['Medicamentos', 'Protección Personal', 'Equipos Médicos', 'Instrumental']
    
    # Monedas válidas
    VALID_CURRENCIES = ['USD', 'COP', 'EUR']
    
    # Clases regulatorias válidas
    VALID_REGULATORY_CLASSES = ['Clase I', 'Clase II', 'Clase IIa', 'Clase IIb', 'Clase III']
    
    # Límites
    MAX_FILE_SIZE_MB = 20
    MAX_ROWS = 10000
    
    def __init__(self):
        """Constructor del validador"""
        self.errors = []
        self.warnings = []
    
    def validate_file_structure(self, file_content: bytes, filename: str) -> Tuple[bool, List[str], int]:
        """
        Fase 1: Validación rápida de estructura del archivo.
        
        Args:
            file_content: Contenido del archivo en bytes
            filename: Nombre del archivo
            
        Returns:
            (is_valid, errors, total_rows)
        """
        self.errors = []
        
        # Validar extensión
        if not filename.lower().endswith('.csv'):
            self.errors.append("El archivo debe tener extensión .csv")
            return False, self.errors, 0
        
        # Validar tamaño
        file_size_mb = len(file_content) / (1024 * 1024)
        if file_size_mb > self.MAX_FILE_SIZE_MB:
            self.errors.append(f"El archivo excede el tamaño máximo de {self.MAX_FILE_SIZE_MB} MB")
            return False, self.errors, 0
        
        # Decodificar y parsear CSV
        try:
            content_str = file_content.decode('utf-8-sig')  # utf-8-sig maneja BOM automáticamente
        except UnicodeDecodeError:
            try:
                content_str = file_content.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    content_str = file_content.decode('latin-1')
                except Exception:
                    self.errors.append("No se pudo decodificar el archivo. Use codificación UTF-8 o Latin-1")
                    return False, self.errors, 0
        
        # Parsear CSV
        try:
            csv_file = io.StringIO(content_str)
            reader = csv.DictReader(csv_file)
            headers = reader.fieldnames
            
            if not headers:
                self.errors.append("El archivo CSV está vacío o no tiene encabezados")
                return False, self.errors, 0
            
            # Validar columnas requeridas
            missing_columns = [col for col in self.REQUIRED_COLUMNS if col not in headers]
            if missing_columns:
                self.errors.append(f"Faltan columnas requeridas: {', '.join(missing_columns)}")
            
            # Validar columnas desconocidas
            all_valid_columns = self.REQUIRED_COLUMNS + self.OPTIONAL_COLUMNS
            unknown_columns = [col for col in headers if col not in all_valid_columns]
            if unknown_columns:
                self.warnings.append(f"Columnas desconocidas (serán ignoradas): {', '.join(unknown_columns)}")
            
            # Contar filas
            rows = list(reader)
            total_rows = len(rows)
            
            if total_rows == 0:
                self.errors.append("El archivo no contiene datos (solo encabezados)")
                return False, self.errors, 0
            
            if total_rows > self.MAX_ROWS:
                self.errors.append(f"El archivo excede el máximo de {self.MAX_ROWS} filas. Tiene {total_rows} filas")
                return False, self.errors, 0
            
            is_valid = len(self.errors) == 0
            return is_valid, self.errors, total_rows
            
        except csv.Error as e:
            self.errors.append(f"Error al parsear CSV: {str(e)}")
            return False, self.errors, 0
        except Exception as e:
            self.errors.append(f"Error inesperado al validar archivo: {str(e)}")
            return False, self.errors, 0
    
    def validate_row_data(self, row: Dict, row_number: int) -> Tuple[bool, Optional[str]]:
        """
        Fase 2: Validación detallada de una fila de datos.
        
        Args:
            row: Diccionario con datos de la fila
            row_number: Número de fila (para reportes de error)
            
        Returns:
            (is_valid, error_message)
        """
        try:
            # Validar campos requeridos no vacíos
            for field in self.REQUIRED_COLUMNS:
                if not row.get(field) or str(row.get(field)).strip() == '':
                    return False, f"Campo requerido '{field}' está vacío"
            
            # Validar SKU
            sku = row['sku'].strip()
            if len(sku) > 100:
                return False, "SKU excede 100 caracteres"
            
            # Validar nombre
            name = row['name'].strip()
            if len(name) > 255:
                return False, "Nombre excede 255 caracteres"
            if len(name) < 3:
                return False, "Nombre debe tener al menos 3 caracteres"
            
            # Validar categoría
            category = row['category'].strip()
            if category not in self.VALID_CATEGORIES:
                return False, f"Categoría '{category}' no válida. Debe ser una de: {', '.join(self.VALID_CATEGORIES)}"
            
            # Validar precio
            try:
                unit_price = Decimal(str(row['unit_price']).strip())
                if unit_price <= 0:
                    return False, "El precio debe ser mayor a 0"
                if unit_price > 999999.99:
                    return False, "El precio excede el máximo permitido"
            except (InvalidOperation, ValueError):
                return False, f"Precio inválido: '{row['unit_price']}'"
            
            # Validar moneda
            currency = row['currency'].strip().upper()
            if currency not in self.VALID_CURRENCIES:
                return False, f"Moneda '{currency}' no válida. Debe ser una de: {', '.join(self.VALID_CURRENCIES)}"
            
            # Validar unidad de medida
            unit_of_measure = row['unit_of_measure'].strip()
            if len(unit_of_measure) > 50:
                return False, "Unidad de medida excede 50 caracteres"
            
            # Validar supplier_id (debe ser numérico)
            try:
                supplier_id = int(row['supplier_id'])
            except ValueError:
                return False, f"Supplier ID debe ser numérico: '{row['supplier_id']}'"
            
            # Validaciones opcionales
            if row.get('requires_cold_chain'):
                requires_cold = str(row['requires_cold_chain']).strip().lower()
                if requires_cold not in ['true', 'false', '1', '0', 'yes', 'no', 'si', 'sí']:
                    return False, f"requires_cold_chain debe ser true/false: '{row['requires_cold_chain']}'"
            
            if row.get('storage_temperature_min'):
                try:
                    temp_min = float(row['storage_temperature_min'])
                    if temp_min < -100 or temp_min > 100:
                        return False, "Temperatura mínima fuera de rango (-100 a 100)"
                except ValueError:
                    return False, f"Temperatura mínima inválida: '{row['storage_temperature_min']}'"
            
            if row.get('storage_temperature_max'):
                try:
                    temp_max = float(row['storage_temperature_max'])
                    if temp_max < -100 or temp_max > 100:
                        return False, "Temperatura máxima fuera de rango (-100 a 100)"
                except ValueError:
                    return False, f"Temperatura máxima inválida: '{row['storage_temperature_max']}'"
            
            if row.get('storage_humidity_max'):
                try:
                    humidity = float(row['storage_humidity_max'])
                    if humidity < 0 or humidity > 100:
                        return False, "Humedad máxima fuera de rango (0 a 100)"
                except ValueError:
                    return False, f"Humedad máxima inválida: '{row['storage_humidity_max']}'"
            
            if row.get('regulatory_class'):
                reg_class = row['regulatory_class'].strip()
                if reg_class and reg_class not in self.VALID_REGULATORY_CLASSES:
                    return False, f"Clase regulatoria '{reg_class}' no válida"
            
            if row.get('weight_kg'):
                try:
                    weight = Decimal(str(row['weight_kg']))
                    if weight < 0:
                        return False, "Peso no puede ser negativo"
                except (InvalidOperation, ValueError):
                    return False, f"Peso inválido: '{row['weight_kg']}'"
            
            return True, None
            
        except Exception as e:
            return False, f"Error al validar fila: {str(e)}"
    
    def validate_business_rules(self, row: Dict, row_number: int) -> Tuple[bool, Optional[str]]:
        """
        Validación de reglas de negocio (consultas a BD).
        
        Args:
            row: Diccionario con datos de la fila
            row_number: Número de fila
            
        Returns:
            (is_valid, error_message)
        """
        try:
            # Validar que SKU no exista en BD
            sku = row['sku'].strip()
            existing_product = Product.query.filter_by(sku=sku).first()
            if existing_product:
                return False, f"SKU '{sku}' ya existe en la base de datos (ID: {existing_product.id})"
            
            # Validar que supplier_id exista
            supplier_id = int(row['supplier_id'])
            supplier = Supplier.query.filter_by(id=supplier_id).first()
            if not supplier:
                return False, f"Supplier ID {supplier_id} no existe"
            
            if not supplier.is_active:
                return False, f"Supplier ID {supplier_id} ({supplier.name}) está inactivo"
            
            # Validar barcode único si existe
            if row.get('barcode'):
                barcode = row['barcode'].strip()
                if barcode:
                    existing_barcode = Product.query.filter_by(barcode=barcode).first()
                    if existing_barcode:
                        return False, f"Código de barras '{barcode}' ya existe (SKU: {existing_barcode.sku})"
            
            # Validar registro sanitario único si existe
            if row.get('sanitary_registration'):
                san_reg = row['sanitary_registration'].strip()
                if san_reg:
                    existing_reg = Product.query.filter_by(sanitary_registration=san_reg).first()
                    if existing_reg:
                        return False, f"Registro sanitario '{san_reg}' ya existe (SKU: {existing_reg.sku})"
            
            return True, None
            
        except Exception as e:
            return False, f"Error en validación de negocio: {str(e)}"
    
    def parse_csv_to_list(self, file_content: bytes) -> List[Dict]:
        """
        Parsea el contenido CSV a una lista de diccionarios.
        
        Args:
            file_content: Contenido del archivo en bytes
            
        Returns:
            Lista de diccionarios con los datos
        """
        try:
            content_str = file_content.decode('utf-8-sig')  # utf-8-sig remueve BOM
        except UnicodeDecodeError:
            try:
                content_str = file_content.decode('utf-8')
            except UnicodeDecodeError:
                content_str = file_content.decode('latin-1')
        
        csv_file = io.StringIO(content_str)
        reader = csv.DictReader(csv_file)
        return list(reader)
