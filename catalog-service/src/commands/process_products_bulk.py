"""
Comando para procesar archivos CSV de productos en background usando threading.
Crea productos masivamente y actualiza el estado del job.
"""
import threading
from typing import Dict
from decimal import Decimal, InvalidOperation
from datetime import datetime
from src.session import db
from src.models.product import Product
from src.models.bulk_upload_job import BulkUploadJob, JobStatus
from src.commands.validate_product_csv import ValidateProductCSV


class ProcessProductsBulk:
    """
    Comando para procesar productos en background desde un CSV.
    Utiliza threading para no bloquear la request HTTP.
    """
    
    def __init__(self, app):
        """
        Constructor del procesador.
        
        Args:
            app: Instancia de la aplicación Flask (necesaria para app_context)
        """
        self.app = app
        self.validator = ValidateProductCSV()
    
    def start_processing(self, job_id: str, csv_data: list) -> None:
        """
        Inicia el procesamiento en un thread separado.
        
        Args:
            job_id: ID del job a procesar
            csv_data: Lista de diccionarios con los datos del CSV
        """
        thread = threading.Thread(
            target=self._process_in_background,
            args=(job_id, csv_data),
            daemon=True
        )
        thread.start()
    
    def _process_in_background(self, job_id: str, csv_data: list) -> None:
        """
        Procesa el CSV en background.
        Esta función corre en un thread separado.
        
        Args:
            job_id: ID del job a procesar
            csv_data: Lista de diccionarios con los datos del CSV
        """
        with self.app.app_context():
            try:
                # Obtener el job
                job = BulkUploadJob.query.filter_by(job_id=job_id).first()
                if not job:
                    print(f"ERROR: Job {job_id} not found")
                    return
                
                # Cambiar estado a processing
                job.set_status(JobStatus.PROCESSING)
                db.session.commit()
                
                # Procesar cada fila
                for row_number, row_data in enumerate(csv_data, start=2):  # start=2 porque la fila 1 son headers
                    try:
                        # Validar datos de la fila
                        is_valid_data, data_error = self.validator.validate_row_data(row_data, row_number)
                        if not is_valid_data:
                            job.add_error(row_number, row_data, data_error)
                            job.increment_failed_rows()
                            job.increment_processed_rows()
                            db.session.commit()
                            continue
                        
                        # Validar reglas de negocio
                        is_valid_business, business_error = self.validator.validate_business_rules(row_data, row_number)
                        if not is_valid_business:
                            job.add_error(row_number, row_data, business_error)
                            job.increment_failed_rows()
                            job.increment_processed_rows()
                            db.session.commit()
                            continue
                        
                        # Crear producto
                        product = self._create_product_from_row(row_data)
                        db.session.add(product)
                        
                        job.increment_successful_rows()
                        job.increment_processed_rows()
                        
                        # Commit cada 50 productos para evitar transacciones muy largas
                        if job.get_processed_rows() % 50 == 0:
                            db.session.commit()
                        
                    except Exception as e:
                        # Error inesperado al procesar esta fila
                        db.session.rollback()
                        error_msg = f"Error inesperado: {str(e)}"
                        job.add_error(row_number, row_data, error_msg)
                        job.increment_failed_rows()
                        job.increment_processed_rows()
                        db.session.commit()
                
                # Commit final
                db.session.commit()
                
                # Actualizar estado final
                job.set_status(JobStatus.COMPLETED)
                db.session.commit()
                
                print(f"Job {job_id} completed: {job.get_successful_rows()}/{job.get_total_rows()} successful")
                
            except Exception as e:
                # Error crítico en el procesamiento
                print(f"CRITICAL ERROR in job {job_id}: {str(e)}")
                try:
                    job = BulkUploadJob.query.filter_by(job_id=job_id).first()
                    if job:
                        job.set_status(JobStatus.FAILED)
                        job.set_error_message(f"Error crítico en el procesamiento: {str(e)}")
                        db.session.commit()
                except Exception as commit_error:
                    print(f"ERROR updating job status: {str(commit_error)}")
    
    def _create_product_from_row(self, row: Dict) -> Product:
        """
        Crea una instancia de Product desde una fila del CSV.
        
        Args:
            row: Diccionario con los datos de la fila
            
        Returns:
            Instancia de Product
        """
        # Convertir valores booleanos
        requires_cold_chain = self._parse_boolean(row.get('requires_cold_chain'))
        requires_prescription = self._parse_boolean(row.get('requires_prescription'))
        is_active = self._parse_boolean(row.get('is_active', 'true'))
        is_discontinued = self._parse_boolean(row.get('is_discontinued', 'false'))
        
        # Convertir valores numéricos opcionales
        storage_temp_min = self._parse_float(row.get('storage_temperature_min'))
        storage_temp_max = self._parse_float(row.get('storage_temperature_max'))
        storage_humidity_max = self._parse_decimal(row.get('storage_humidity_max'))
        weight_kg = self._parse_decimal(row.get('weight_kg'))
        length_cm = self._parse_decimal(row.get('length_cm'))
        width_cm = self._parse_decimal(row.get('width_cm'))
        height_cm = self._parse_decimal(row.get('height_cm'))
        
        # Crear producto
        product = Product(
            sku=row['sku'].strip(),
            name=row['name'].strip(),
            description=row.get('description', '').strip() or None,
            category=row['category'].strip(),
            subcategory=row.get('subcategory', '').strip() or None,
            unit_price=Decimal(str(row['unit_price'])),
            currency=row['currency'].strip().upper(),
            unit_of_measure=row['unit_of_measure'].strip(),
            supplier_id=int(row['supplier_id']),
            requires_cold_chain=requires_cold_chain,
            storage_temperature_min=storage_temp_min,
            storage_temperature_max=storage_temp_max,
            storage_humidity_max=storage_humidity_max,
            sanitary_registration=row.get('sanitary_registration', '').strip() or None,
            requires_prescription=requires_prescription,
            regulatory_class=row.get('regulatory_class', '').strip() or None,
            weight_kg=weight_kg,
            length_cm=length_cm,
            width_cm=width_cm,
            height_cm=height_cm,
            manufacturer=row.get('manufacturer', '').strip() or None,
            country_of_origin=row.get('country_of_origin', '').strip() or None,
            barcode=row.get('barcode', '').strip() or None,
            image_url=row.get('image_url', '').strip() or None,
            is_active=is_active,
            is_discontinued=is_discontinued
        )
        
        return product
    
    def _parse_boolean(self, value) -> bool:
        """Convierte string a booleano"""
        if not value:
            return False
        
        value_str = str(value).strip().lower()
        return value_str in ['true', '1', 'yes', 'si', 'sí', 't', 'y']
    
    def _parse_float(self, value) -> float:
        """Convierte string a float, retorna None si está vacío"""
        if not value or str(value).strip() == '':
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def _parse_decimal(self, value) -> Decimal:
        """Convierte string a Decimal, retorna None si está vacío"""
        if not value or str(value).strip() == '':
            return None
        try:
            return Decimal(str(value))
        except (ValueError, TypeError, InvalidOperation):
            return None
