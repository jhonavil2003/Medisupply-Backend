"""
Background jobs para el servicio de logística.

Jobs:
- expire_cart_reservations: Expira reservas de carrito antiguas cada minuto
"""

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from src.commands.cart_reservations import ExpireCartReservationsCommand

logger = logging.getLogger(__name__)

# Instancia global del scheduler
scheduler = None


def expire_cart_reservations_job():
    """
    Job que expira reservas de carrito que hayan superado su TTL.
    
    Se ejecuta cada minuto.
    """
    try:
        logger.info("🔄 Ejecutando job de expiración de reservas de carrito...")
        
        command = ExpireCartReservationsCommand()
        result = command.execute()
        
        if result['expired_count'] > 0:
            logger.info(
                f"✅ Expiradas {result['expired_count']} reservas - "
                f"Productos afectados: {result.get('products_affected', [])}"
            )
        else:
            logger.debug("No hay reservas para expirar")
            
    except Exception as e:
        logger.error(f"❌ Error en job de expiración de reservas: {str(e)}", exc_info=True)


def init_background_jobs(app):
    """
    Inicializa y configura los background jobs.
    
    Args:
        app: Instancia de Flask app
    """
    global scheduler
    
    if scheduler is not None:
        logger.warning("⚠️ Scheduler ya está inicializado")
        return scheduler
    
    logger.info("🚀 Inicializando background jobs...")
    
    # Crear scheduler
    scheduler = BackgroundScheduler(daemon=True)
    
    # Función wrapper que ejecuta el job dentro del app context
    def run_job_with_context():
        with app.app_context():
            expire_cart_reservations_job()
    
    # Configurar job de expiración de reservas (cada minuto)
    scheduler.add_job(
        func=run_job_with_context,
        trigger=CronTrigger(minute='*'),  # Cada minuto
        id='expire_cart_reservations',
        name='Expirar reservas de carrito',
        replace_existing=True,
        max_instances=1  # Solo una instancia del job a la vez
    )
    
    # Iniciar scheduler
    scheduler.start()
    
    logger.info("✅ Background jobs iniciados correctamente")
    logger.info("  - expire_cart_reservations: Cada minuto")
    
    return scheduler


def shutdown_background_jobs():
    """Detiene todos los background jobs."""
    global scheduler
    
    if scheduler is not None:
        logger.info("🛑 Deteniendo background jobs...")
        scheduler.shutdown(wait=False)
        scheduler = None
        logger.info("✅ Background jobs detenidos")


def get_scheduler():
    """Obtiene la instancia del scheduler."""
    return scheduler
