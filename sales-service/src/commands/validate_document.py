"""
Comando para validar la existencia de un documento (RUC/NIT) en el sistema.
"""

from src.models.customer import Customer


class ValidateDocument:
    """
    Comando para validar si un número de documento ya existe en el sistema.
    
    Permite verificar si un RUC/NIT ya está registrado antes de crear un cliente,
    útil para validaciones en el frontend y evitar duplicados.
    """
    
    def __init__(self, document_number: str, document_type: str = "NIT"):
        """
        Inicializa el comando de validación.
        
        Args:
            document_number (str): Número de documento a validar
            document_type (str): Tipo de documento (NIT, CC, CE, RUT, DNI)
        """
        self.document_number = document_number.strip()
        self.document_type = document_type.strip().upper()
        
        if not self.document_number:
            raise ValueError("document_number is required")
        
        if not self.document_type:
            raise ValueError("document_type is required")
    
    def execute(self) -> dict:
        """
        Ejecuta la validación del documento.
        
        Returns:
            dict: Diccionario con el resultado de la validación
                - exists (bool): True si el documento existe, False si está disponible
                - customer_id (int, opcional): ID del cliente si existe
                - message (str): Mensaje descriptivo del resultado
        
        Raises:
            Exception: Si hay un error en la consulta a la base de datos
        """
        try:
            # Buscar cliente por número y tipo de documento
            customer = Customer.query.filter(
                Customer.document_number == self.document_number,
                Customer.document_type == self.document_type
            ).first()
            
            if customer:
                return {
                    "exists": True,
                    "customer_id": customer.id,
                    "message": f"Document {self.document_type} {self.document_number} is already registered to customer: {customer.business_name}"
                }
            else:
                return {
                    "exists": False,
                    "customer_id": None,
                    "message": f"Document {self.document_type} {self.document_number} is available for registration"
                }
                
        except Exception as e:
            raise Exception(f"Error validating document: {str(e)}")