from src.session import db
from datetime import datetime
from typing import Optional, List, Dict
import uuid
from sqlalchemy.orm.attributes import flag_modified


class JobStatus:
    """Estados posibles de un job de carga masiva"""
    PENDING = 'pending'
    VALIDATING = 'validating'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'


class BulkUploadJob(db.Model):
    """Entidad para tracking de jobs de carga masiva de productos"""
    
    __tablename__ = 'bulk_upload_jobs'

    # Primary Key
    id = db.Column(db.Integer, primary_key=True)
    
    # Job Identification
    job_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    filename = db.Column(db.String(255), nullable=False)
    
    # Status Tracking
    status = db.Column(db.String(20), nullable=False, default=JobStatus.PENDING, index=True)
    
    # Progress Metrics
    total_rows = db.Column(db.Integer, nullable=False, default=0)
    processed_rows = db.Column(db.Integer, nullable=False, default=0)
    successful_rows = db.Column(db.Integer, nullable=False, default=0)
    failed_rows = db.Column(db.Integer, nullable=False, default=0)
    
    # Error Tracking (JSON array of error objects)
    errors = db.Column(db.JSON, nullable=True)
    
    # Metadata
    created_by = db.Column(db.String(100), nullable=True)
    file_size_bytes = db.Column(db.Integer, nullable=True)
    file_hash = db.Column(db.String(64), nullable=True)  # SHA256 hash del archivo
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp(), nullable=False)
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Processing Details
    processing_time_seconds = db.Column(db.Float, nullable=True)
    error_message = db.Column(db.Text, nullable=True)  # Error general si el job falla completamente

    def __init__(self, filename: str, total_rows: int = 0, created_by: str = None, 
                 file_size_bytes: int = None, file_hash: str = None):
        """Constructor del job"""
        self.job_id = str(uuid.uuid4())
        self.filename = filename
        self.status = JobStatus.PENDING
        self.total_rows = total_rows
        self.processed_rows = 0
        self.successful_rows = 0
        self.failed_rows = 0
        self.errors = []
        self.created_by = created_by
        self.file_size_bytes = file_size_bytes
        self.file_hash = file_hash

    def __repr__(self):
        return f"<BulkUploadJob(id={self.id}, job_id='{self.job_id}', status='{self.status}')>"

    # Getters and Setters (Java style)
    def get_id(self) -> Optional[int]:
        return self.id
    
    def get_job_id(self) -> str:
        return self.job_id
    
    def get_filename(self) -> str:
        return self.filename
    
    def get_status(self) -> str:
        return self.status
    
    def set_status(self, status: str):
        """Cambia el estado del job y actualiza timestamps"""
        self.status = status
        if status == JobStatus.PROCESSING and not self.started_at:
            self.started_at = datetime.utcnow()
        elif status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
            if not self.completed_at:
                self.completed_at = datetime.utcnow()
            if self.started_at:
                self.processing_time_seconds = (self.completed_at - self.started_at).total_seconds()
    
    def get_total_rows(self) -> int:
        return self.total_rows
    
    def set_total_rows(self, total_rows: int):
        self.total_rows = total_rows
    
    def get_processed_rows(self) -> int:
        return self.processed_rows
    
    def increment_processed_rows(self):
        """Incrementa el contador de filas procesadas"""
        self.processed_rows += 1
    
    def get_successful_rows(self) -> int:
        return self.successful_rows
    
    def increment_successful_rows(self):
        """Incrementa el contador de filas exitosas"""
        self.successful_rows += 1
    
    def get_failed_rows(self) -> int:
        return self.failed_rows
    
    def increment_failed_rows(self):
        """Incrementa el contador de filas fallidas"""
        self.failed_rows += 1
    
    def get_errors(self) -> List[Dict]:
        return self.errors or []
    
    def add_error(self, row_number: int, row_data: Dict, error_message: str):
        """Agrega un error a la lista"""
        if self.errors is None:
            self.errors = []
        
        error_entry = {
            'row': row_number,
            'data': row_data,
            'error': error_message
        }
        self.errors.append(error_entry)
        # Marcar campo JSONB como modificado para SQLAlchemy
        flag_modified(self, 'errors')
    
    def get_created_by(self) -> Optional[str]:
        return self.created_by
    
    def get_created_at(self) -> datetime:
        return self.created_at
    
    def get_completed_at(self) -> Optional[datetime]:
        return self.completed_at
    
    def set_error_message(self, error_message: str):
        """Establece un mensaje de error general"""
        self.error_message = error_message

    # Business Methods
    def get_progress_percentage(self) -> float:
        """Calcula el porcentaje de progreso"""
        if self.total_rows == 0:
            return 0.0
        return round((self.processed_rows / self.total_rows) * 100, 2)
    
    def get_success_rate(self) -> float:
        """Calcula el porcentaje de éxito"""
        if self.processed_rows == 0:
            return 0.0
        return round((self.successful_rows / self.processed_rows) * 100, 2)
    
    def is_completed(self) -> bool:
        """Verifica si el job está completado"""
        return self.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]
    
    def is_in_progress(self) -> bool:
        """Verifica si el job está en progreso"""
        return self.status in [JobStatus.VALIDATING, JobStatus.PROCESSING]
    
    def can_be_cancelled(self) -> bool:
        """Verifica si el job puede ser cancelado"""
        return self.status in [JobStatus.PENDING, JobStatus.VALIDATING]
    
    def get_estimated_time_remaining(self) -> Optional[float]:
        """Estima el tiempo restante en segundos"""
        if not self.started_at or self.processed_rows == 0:
            return None
        
        elapsed = (datetime.utcnow() - self.started_at).total_seconds()
        avg_time_per_row = elapsed / self.processed_rows
        remaining_rows = self.total_rows - self.processed_rows
        
        return round(avg_time_per_row * remaining_rows, 2)

    def to_dict(self, include_errors: bool = False) -> dict:
        """Convierte la entidad a diccionario para serialización JSON"""
        result = {
            'id': self.id,
            'job_id': self.job_id,
            'filename': self.filename,
            'status': self.status,
            'total_rows': self.total_rows,
            'processed_rows': self.processed_rows,
            'successful_rows': self.successful_rows,
            'failed_rows': self.failed_rows,
            'progress_percentage': self.get_progress_percentage(),
            'success_rate': self.get_success_rate(),
            'created_by': self.created_by,
            'file_size_bytes': self.file_size_bytes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'processing_time_seconds': self.processing_time_seconds,
            'estimated_time_remaining': self.get_estimated_time_remaining(),
            'error_message': self.error_message
        }
        
        if include_errors:
            result['errors'] = self.get_errors()
            result['error_count'] = len(self.get_errors())
        else:
            result['error_count'] = len(self.get_errors())
        
        return result
    
    def to_summary_dict(self) -> dict:
        """Versión resumida para listados"""
        return {
            'job_id': self.job_id,
            'filename': self.filename,
            'status': self.status,
            'total_rows': self.total_rows,
            'successful_rows': self.successful_rows,
            'failed_rows': self.failed_rows,
            'progress_percentage': self.get_progress_percentage(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
