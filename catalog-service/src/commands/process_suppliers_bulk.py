"""
Comando para procesar archivos CSV de suppliers en background usando threading.
Crea suppliers masivamente y actualiza el estado del job.
"""
import threading
from typing import Dict
from decimal import Decimal, InvalidOperation
from datetime import datetime
from src.session import db
from src.models.supplier import Supplier
from src.models.bulk_upload_supplier_job import BulkUploadSupplierJob, JobStatus
from src.commands.validate_supplier_csv import ValidateSupplierCSV


class ProcessSuppliersBulk:
    """
    Comando para procesar suppliers en background desde un CSV.
    Utiliza threading para no bloquear la request HTTP.
    """
    
    def __init__(self, app):
        """
        Constructor del procesador.
        
        Args:
            app: Instancia de la aplicación Flask (necesaria para app_context)
        """
        self.app = app
        self.validator = ValidateSupplierCSV()
    
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
                job = BulkUploadSupplierJob.query.filter_by(job_id=job_id).first()
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
                        
                        # Crear supplier
                        supplier = self._create_supplier_from_row(row_data)
                        db.session.add(supplier)
                        
                        job.increment_successful_rows()
                        job.increment_processed_rows()
                        
                        # Commit cada 50 suppliers para evitar transacciones muy largas
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
                    job = BulkUploadSupplierJob.query.filter_by(job_id=job_id).first()
                    if job:
                        job.set_status(JobStatus.FAILED)
                        job.set_error_message(f"Error crítico en el procesamiento: {str(e)}")
                        db.session.commit()
                except Exception as commit_error:
                    print(f"ERROR updating job status: {str(commit_error)}")
    
    def _create_supplier_from_row(self, row: Dict) -> Supplier:
        """
        Crea una instancia de Supplier desde una fila del CSV.
        
        Args:
            row: Diccionario con los datos de la fila
            
        Returns:
            Instancia de Supplier
        """
        # Convertir valores booleanos
        is_certified = self._parse_boolean(row.get('is_certified', 'false'))
        is_active = self._parse_boolean(row.get('is_active', 'true'))
        
        # Convertir credit_limit si está presente
        credit_limit = self._parse_decimal(row.get('credit_limit'))
        
        # Parsear fechas si están presentes
        certification_date = self._parse_date(row.get('certification_date'))
        certification_expiry = self._parse_date(row.get('certification_expiry'))
        
        # Crear supplier
        supplier = Supplier(
            tax_id=row['tax_id'].strip(),
            name=row['name'].strip(),
            legal_name=row.get('legal_name', '').strip() or row['name'].strip(),  # Usar name si no hay legal_name
            email=row['email'].strip(),
            phone=row['phone'].strip(),
            website=row.get('website', '').strip() or None,
            address_line1=row['address_line1'].strip(),
            address_line2=row.get('address_line2', '').strip() or None,
            city=row.get('city', '').strip() or None,
            state=row.get('state', '').strip() or None,
            country=row['country'].strip(),
            postal_code=row.get('postal_code', '').strip() or None,
            payment_terms=row.get('payment_terms', '').strip() or None,
            credit_limit=credit_limit,
            currency=row.get('currency', '').strip().upper() or None,
            is_certified=is_certified,
            certification_date=certification_date,
            certification_expiry=certification_expiry,
            is_active=is_active
        )
        
        return supplier
    
    def _parse_boolean(self, value) -> bool:
        """Convierte string a booleano"""
        if not value:
            return False
        
        value_str = str(value).strip().lower()
        return value_str in ['true', '1', 'yes', 'si', 'sí', 't', 'y']
    
    def _parse_decimal(self, value) -> Decimal:
        """Convierte string a Decimal, retorna None si está vacío"""
        if not value or str(value).strip() == '':
            return None
        try:
            return Decimal(str(value))
        except (ValueError, TypeError, InvalidOperation):
            return None
    
    def _parse_date(self, value):
        """Convierte string a date, retorna None si está vacío"""
        if not value or str(value).strip() == '':
            return None
        try:
            from datetime import datetime
            return datetime.strptime(str(value).strip(), '%Y-%m-%d').date()
        except (ValueError, TypeError):
            return None
