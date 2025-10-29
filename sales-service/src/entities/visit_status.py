from enum import Enum


class VisitStatus(Enum):
    """Enum para estados de visitas"""
    SCHEDULED = "SCHEDULED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    
    def __str__(self):
        return self.value
    
    @classmethod
    def from_string(cls, status_str):
        """Crea un VisitStatus desde string"""
        try:
            return cls(status_str)
        except ValueError:
            return cls.SCHEDULED  # Default fallback