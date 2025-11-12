"""
Comando para validar archivos CSV de carga masiva de suppliers.
Valida estructura, tipos de datos y reglas de negocio.
"""
import csv
import io
import re
from typing import Dict, List, Tuple, Optional
from src.models.supplier import Supplier
from src.session import db


class CSVValidationError(Exception):
    """Excepción personalizada para errores de validación de CSV"""
    pass


class ValidateSupplierCSV:
    """
    Comando para validar archivos CSV de suppliers.
    Realiza validaciones de estructura y contenido en dos fases.
    """
    
    # Columnas requeridas en el CSV
    REQUIRED_COLUMNS = [
        'tax_id', 'name', 'address_line1', 'phone', 'email', 'country'
    ]
    
    # Columnas opcionales permitidas
    OPTIONAL_COLUMNS = [
        'legal_name', 'website', 'address_line2', 'city', 'state', 
        'postal_code', 'payment_terms', 'credit_limit', 'currency',
        'is_certified', 'certification_date', 'certification_expiry', 'is_active'
    ]
    
    # Monedas válidas
    VALID_CURRENCIES = ['USD', 'COP', 'EUR']
    
    # Países válidos (lista simplificada - expandir según necesidad)
    VALID_COUNTRIES = [
        'Colombia', 'Estados Unidos', 'México', 'Argentina', 'Chile', 
        'Perú', 'Ecuador', 'Venezuela', 'Brasil', 'España'
    ]
    
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
            
            # Advertir sobre columnas desconocidas
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
            
            # Validar tax_id (RUC)
            tax_id = row['tax_id'].strip()
            if len(tax_id) < 5 or len(tax_id) > 50:
                return False, "RUC/Tax ID debe tener entre 5 y 50 caracteres"
            
            # Validar nombre
            name = row['name'].strip()
            if len(name) < 3:
                return False, "Nombre debe tener al menos 3 caracteres"
            if len(name) > 255:
                return False, "Nombre excede 255 caracteres"
            
            # Validar legal_name si está presente
            if row.get('legal_name') and str(row.get('legal_name')).strip():
                legal_name = row['legal_name'].strip()
                if len(legal_name) > 255:
                    return False, "Nombre legal excede 255 caracteres"
            
            # Validar email
            email = row['email'].strip()
            if not self._is_valid_email(email):
                return False, f"Email '{email}' no es válido"
            
            # Validar phone
            phone = row['phone'].strip()
            if len(phone) < 7 or len(phone) > 50:
                return False, "Teléfono debe tener entre 7 y 50 caracteres"
            
            # Validar address_line1
            address = row['address_line1'].strip()
            if len(address) < 5:
                return False, "Dirección debe tener al menos 5 caracteres"
            if len(address) > 255:
                return False, "Dirección excede 255 caracteres"
            
            # Validar country
            country = row['country'].strip()
            if country not in self.VALID_COUNTRIES:
                return False, f"País '{country}' no está en la lista válida. Países válidos: {', '.join(self.VALID_COUNTRIES)}"
            
            # Validar campos opcionales
            if row.get('website') and str(row.get('website')).strip():
                website = row['website'].strip()
                if len(website) > 255:
                    return False, "Website excede 255 caracteres"
            
            # Validar currency si está presente
            if row.get('currency') and str(row.get('currency')).strip():
                currency = row['currency'].strip().upper()
                if currency not in self.VALID_CURRENCIES:
                    return False, f"Moneda '{currency}' no válida. Valores permitidos: {', '.join(self.VALID_CURRENCIES)}"
            
            # Validar credit_limit si está presente
            if row.get('credit_limit') and str(row.get('credit_limit')).strip():
                try:
                    credit_limit = float(row['credit_limit'])
                    if credit_limit < 0:
                        return False, "Límite de crédito no puede ser negativo"
                    if credit_limit > 999999999999.99:
                        return False, "Límite de crédito excede el valor máximo permitido"
                except ValueError:
                    return False, f"Límite de crédito '{row['credit_limit']}' no es un número válido"
            
            # Validar booleanos
            bool_fields = ['is_certified', 'is_active']
            for field in bool_fields:
                if row.get(field) and str(row.get(field)).strip():
                    value = str(row.get(field)).strip().lower()
                    if value not in ['true', 'false', '1', '0', 'yes', 'no', 'si', 'sí', 't', 'f', 'y', 'n']:
                        return False, f"Campo '{field}' debe ser true/false, 1/0, yes/no, si/no"
            
            # Validar fechas si están presentes
            date_fields = ['certification_date', 'certification_expiry']
            for field in date_fields:
                if row.get(field) and str(row.get(field)).strip():
                    date_value = row[field].strip()
                    if not self._is_valid_date(date_value):
                        return False, f"Fecha '{field}' no válida. Formato esperado: YYYY-MM-DD"
            
            return True, None
            
        except Exception as e:
            return False, f"Error al validar fila: {str(e)}"
    
    def validate_business_rules(self, row: Dict, row_number: int) -> Tuple[bool, Optional[str]]:
        """
        Fase 3: Validación de reglas de negocio.
        
        Args:
            row: Diccionario con datos de la fila
            row_number: Número de fila
            
        Returns:
            (is_valid, error_message)
        """
        try:
            tax_id = row['tax_id'].strip()
            
            # Verificar que el tax_id no exista ya
            existing_supplier = Supplier.query.filter_by(tax_id=tax_id).first()
            if existing_supplier:
                return False, f"Ya existe un proveedor con RUC/Tax ID '{tax_id}'"
            
            return True, None
            
        except Exception as e:
            return False, f"Error al validar reglas de negocio: {str(e)}"
    
    def parse_csv_to_list(self, file_content: bytes) -> List[Dict]:
        """
        Parsea el archivo CSV y retorna una lista de diccionarios.
        
        Args:
            file_content: Contenido del archivo en bytes
            
        Returns:
            Lista de diccionarios con los datos del CSV
        """
        try:
            content_str = file_content.decode('utf-8-sig')
        except UnicodeDecodeError:
            try:
                content_str = file_content.decode('utf-8')
            except UnicodeDecodeError:
                content_str = file_content.decode('latin-1')
        
        csv_file = io.StringIO(content_str)
        reader = csv.DictReader(csv_file)
        return list(reader)
    
    def _is_valid_email(self, email: str) -> bool:
        """Valida formato de email básico"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _is_valid_date(self, date_str: str) -> bool:
        """Valida formato de fecha YYYY-MM-DD"""
        pattern = r'^\d{4}-\d{2}-\d{2}$'
        if not re.match(pattern, date_str):
            return False
        
        # Validar que sea una fecha válida
        try:
            from datetime import datetime
            datetime.strptime(date_str, '%Y-%m-%d')
            return True
        except ValueError:
            return False
