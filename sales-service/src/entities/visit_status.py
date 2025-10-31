from enum import Enum


class VisitStatus(Enum):
    """Enum para estados de visitas"""
    PROGRAMADA = "PROGRAMADA"     # Estado por defecto al crear/editar
    COMPLETADA = "COMPLETADA"     # Solo mediante botón "Completar"  
    ELIMINADA = "ELIMINADA"       # Solo mediante botón "Eliminar"
    
    def __str__(self):
        return self.value
    
    @classmethod
    def from_string(cls, status_str):
        """Crea un VisitStatus desde string"""
        status_mapping = {
            "PROGRAMADA": cls.PROGRAMADA,
            "programada": cls.PROGRAMADA,
            "SCHEDULED": cls.PROGRAMADA,  # Backward compatibility
            "scheduled": cls.PROGRAMADA,
            "COMPLETADA": cls.COMPLETADA,
            "completada": cls.COMPLETADA,
            "COMPLETED": cls.COMPLETADA,  # Backward compatibility
            "completed": cls.COMPLETADA,
            "ELIMINADA": cls.ELIMINADA,
            "eliminada": cls.ELIMINADA,
            "DELETED": cls.ELIMINADA,     # Backward compatibility
            "deleted": cls.ELIMINADA,
            "CANCELLED": cls.ELIMINADA,   # Backward compatibility
            "cancelled": cls.ELIMINADA
        }
        
        try:
            return status_mapping.get(status_str, cls.PROGRAMADA)
        except Exception:
            return cls.PROGRAMADA  # Default fallback