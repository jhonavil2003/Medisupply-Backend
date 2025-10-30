"""
Comando simplificado para crear visitas
"""
from src.entities.visit import Visit
from src.entities.salesperson import Salesperson
from src.entities.visit_status import VisitStatus
from src.session import db
from datetime import datetime


class CreateVisit:
    """Comando para crear una nueva visita"""
    
    def execute(self, visit_data):
        """Ejecuta la creación de una visita"""
        try:
            # Crear nueva visita
            visit = Visit(
                customer_id=visit_data.customer_id,
                salesperson_id=visit_data.salesperson_id,
                visit_date=visit_data.visit_date,
                visit_time=visit_data.visit_time,
                contacted_persons=getattr(visit_data, 'contacted_persons', None),
                clinical_findings=getattr(visit_data, 'clinical_findings', None),
                additional_notes=getattr(visit_data, 'additional_notes', None),
                address=getattr(visit_data, 'address', None),
                latitude=getattr(visit_data, 'latitude', None),
                longitude=getattr(visit_data, 'longitude', None),
                status=VisitStatus.SCHEDULED
            )
            
            # Guardar en base de datos
            db.session.add(visit)
            db.session.commit()
            
            return visit
            
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Error al crear visita: {str(e)}")