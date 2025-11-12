"""
Modelo para tracking de jobs de carga masiva de suppliers.
Maneja estados, progreso y errores del procesamiento.
"""
import uuid
import json
from datetime import datetime
from enum import Enum
from src.session import db


class JobStatus(str, Enum):
    """Estados posibles de un job de carga masiva"""
    PENDING = 'pending'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'


class BulkUploadSupplierJob(db.Model):
    """
    Modelo para tracking de jobs de carga masiva de suppliers.
    Almacena información del progreso y errores del procesamiento.
    """
    __tablename__ = 'bulk_upload_supplier_jobs'
    
    # Primary Key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    job_id = db.Column(db.String(36), unique=True, nullable=False, index=True)
    
    # Información del archivo
    filename = db.Column(db.String(255), nullable=False)
    file_size_bytes = db.Column(db.Integer)
    
    # Estado del job
    status = db.Column(db.String(20), default=JobStatus.PENDING, nullable=False, index=True)
    
    # Progreso
    total_rows = db.Column(db.Integer, default=0)
    processed_rows = db.Column(db.Integer, default=0)
    successful_rows = db.Column(db.Integer, default=0)
    failed_rows = db.Column(db.Integer, default=0)
    
    # Errores
    errors = db.Column(db.Text)  # JSON con lista de errores
    error_message = db.Column(db.Text)  # Mensaje de error general si el job falla
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    
    def __init__(self, filename: str, total_rows: int = 0, file_size_bytes: int = None):
        """
        Constructor del job.
        
        Args:
            filename: Nombre del archivo CSV
            total_rows: Número total de filas a procesar
            file_size_bytes: Tamaño del archivo en bytes
        """
        self.job_id = str(uuid.uuid4())
        self.filename = filename
        self.total_rows = total_rows
        self.file_size_bytes = file_size_bytes
        self.status = JobStatus.PENDING
        self.processed_rows = 0
        self.successful_rows = 0
        self.failed_rows = 0
        self.errors = json.dumps([])
    
    def set_status(self, status: JobStatus) -> None:
        """
        Actualiza el estado del job.
        
        Args:
            status: Nuevo estado del job
        """
        self.status = status
        
        if status == JobStatus.PROCESSING and not self.started_at:
            self.started_at = datetime.utcnow()
        
        if status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
            self.completed_at = datetime.utcnow()
    
    def increment_processed_rows(self) -> None:
        """Incrementa el contador de filas procesadas"""
        self.processed_rows += 1
    
    def increment_successful_rows(self) -> None:
        """Incrementa el contador de filas exitosas"""
        self.successful_rows += 1
    
    def increment_failed_rows(self) -> None:
        """Incrementa el contador de filas fallidas"""
        self.failed_rows += 1
    
    def add_error(self, row_number: int, row_data: dict, error_message: str) -> None:
        """
        Agrega un error a la lista de errores.
        
        Args:
            row_number: Número de fila con error
            row_data: Datos de la fila
            error_message: Mensaje de error
        """
        errors_list = json.loads(self.errors)
        errors_list.append({
            'row': row_number,
            'data': row_data,
            'error': error_message
        })
        self.errors = json.dumps(errors_list)
    
    def get_errors(self) -> list:
        """
        Obtiene la lista de errores.
        
        Returns:
            Lista de diccionarios con los errores
        """
        return json.loads(self.errors) if self.errors else []
    
    def set_error_message(self, message: str) -> None:
        """
        Establece un mensaje de error general.
        
        Args:
            message: Mensaje de error
        """
        self.error_message = message
    
    def get_progress_percentage(self) -> float:
        """
        Calcula el porcentaje de progreso.
        
        Returns:
            Porcentaje de progreso (0-100)
        """
        if self.total_rows == 0:
            return 0.0
        return round((self.processed_rows / self.total_rows) * 100, 2)
    
    def get_total_rows(self) -> int:
        """Obtiene el total de filas"""
        return self.total_rows
    
    def get_processed_rows(self) -> int:
        """Obtiene las filas procesadas"""
        return self.processed_rows
    
    def get_successful_rows(self) -> int:
        """Obtiene las filas exitosas"""
        return self.successful_rows
    
    def get_failed_rows(self) -> int:
        """Obtiene las filas fallidas"""
        return self.failed_rows
    
    def to_dict(self) -> dict:
        """
        Convierte el job a diccionario.
        
        Returns:
            Diccionario con la información del job
        """
        return {
            'job_id': self.job_id,
            'filename': self.filename,
            'file_size_bytes': self.file_size_bytes,
            'status': self.status,
            'progress': {
                'total_rows': self.total_rows,
                'processed_rows': self.processed_rows,
                'successful_rows': self.successful_rows,
                'failed_rows': self.failed_rows,
                'percentage': self.get_progress_percentage()
            },
            'error_message': self.error_message,
            'timestamps': {
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'started_at': self.started_at.isoformat() if self.started_at else None,
                'completed_at': self.completed_at.isoformat() if self.completed_at else None
            }
        }
    
    def __repr__(self):
        return f'<BulkUploadSupplierJob(id={self.id}, job_id={self.job_id}, status={self.status})>'
