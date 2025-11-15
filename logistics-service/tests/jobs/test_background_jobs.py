"""
Tests para background jobs del servicio de logística.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.jobs.background_jobs import (
    expire_cart_reservations_job,
    init_background_jobs,
    shutdown_background_jobs,
    get_scheduler
)


class TestExpireCartReservationsJob:
    """Tests para el job de expiración de reservas."""
    
    @patch('src.jobs.background_jobs.ExpireCartReservationsCommand')
    def test_expire_cart_reservations_job_success(self, mock_command_class):
        """Test: Job ejecuta comando y registra resultados."""
        # Mock del comando
        mock_command = Mock()
        mock_command.execute.return_value = {
            'expired_count': 5,
            'products_affected': ['PROD-001', 'PROD-002']
        }
        mock_command_class.return_value = mock_command
        
        # Ejecutar job
        expire_cart_reservations_job()
        
        # Verificar que se ejecutó el comando
        mock_command_class.assert_called_once()
        mock_command.execute.assert_called_once()
    
    @patch('src.jobs.background_jobs.ExpireCartReservationsCommand')
    def test_expire_cart_reservations_job_no_expirations(self, mock_command_class):
        """Test: Job cuando no hay reservas para expirar."""
        mock_command = Mock()
        mock_command.execute.return_value = {
            'expired_count': 0,
            'products_affected': []
        }
        mock_command_class.return_value = mock_command
        
        # Ejecutar job (no debe lanzar error)
        expire_cart_reservations_job()
        
        mock_command.execute.assert_called_once()
    
    @patch('src.jobs.background_jobs.ExpireCartReservationsCommand')
    def test_expire_cart_reservations_job_handles_errors(self, mock_command_class):
        """Test: Job maneja errores sin fallar."""
        # Mock que lanza excepción
        mock_command = Mock()
        mock_command.execute.side_effect = Exception("Database error")
        mock_command_class.return_value = mock_command
        
        # Ejecutar job (no debe propagar la excepción)
        expire_cart_reservations_job()
        
        mock_command.execute.assert_called_once()


class TestInitBackgroundJobs:
    """Tests para inicialización de background jobs."""
    
    def test_init_background_jobs_creates_scheduler(self, app):
        """Test: Inicializar jobs crea un scheduler."""
        # Limpiar scheduler global primero
        import src.jobs.background_jobs as bg_module
        bg_module.scheduler = None
        
        scheduler = init_background_jobs(app)
        
        assert scheduler is not None
        assert scheduler.running
        
        # Limpiar
        shutdown_background_jobs()
    
    def test_init_background_jobs_idempotent(self, app):
        """Test: Llamar init múltiples veces no crea múltiples schedulers."""
        import src.jobs.background_jobs as bg_module
        bg_module.scheduler = None
        
        scheduler1 = init_background_jobs(app)
        scheduler2 = init_background_jobs(app)
        
        # Debe retornar el mismo scheduler
        assert scheduler1 is scheduler2
        
        # Limpiar
        shutdown_background_jobs()
    
    def test_init_background_jobs_adds_job(self, app):
        """Test: Inicializar agrega el job de expiración."""
        import src.jobs.background_jobs as bg_module
        bg_module.scheduler = None
        
        scheduler = init_background_jobs(app)
        
        # Verificar que el job existe
        jobs = scheduler.get_jobs()
        assert len(jobs) > 0
        
        job_ids = [job.id for job in jobs]
        assert 'expire_cart_reservations' in job_ids
        
        # Limpiar
        shutdown_background_jobs()


class TestShutdownBackgroundJobs:
    """Tests para detener background jobs."""
    
    def test_shutdown_background_jobs(self, app):
        """Test: Shutdown detiene el scheduler."""
        import src.jobs.background_jobs as bg_module
        bg_module.scheduler = None
        
        # Iniciar scheduler
        init_background_jobs(app)
        
        # Detener
        shutdown_background_jobs()
        
        # Verificar que scheduler es None
        scheduler = get_scheduler()
        assert scheduler is None
    
    def test_shutdown_without_init(self):
        """Test: Shutdown sin scheduler inicializado no falla."""
        import src.jobs.background_jobs as bg_module
        bg_module.scheduler = None
        
        # No debe lanzar error
        shutdown_background_jobs()


class TestGetScheduler:
    """Tests para obtener scheduler."""
    
    def test_get_scheduler_returns_scheduler(self, app):
        """Test: get_scheduler retorna el scheduler activo."""
        import src.jobs.background_jobs as bg_module
        bg_module.scheduler = None
        
        init_background_jobs(app)
        scheduler = get_scheduler()
        
        assert scheduler is not None
        
        # Limpiar
        shutdown_background_jobs()
    
    def test_get_scheduler_when_none(self):
        """Test: get_scheduler retorna None si no hay scheduler."""
        import src.jobs.background_jobs as bg_module
        bg_module.scheduler = None
        
        scheduler = get_scheduler()
        assert scheduler is None
