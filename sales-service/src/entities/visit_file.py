from src.session import db


class VisitFile(db.Model):
    """Entidad VisitFile - Representa un archivo adjunto a una visita"""
    
    __tablename__ = 'visit_files'

    id = db.Column(db.Integer, primary_key=True)
    visit_id = db.Column(db.Integer, db.ForeignKey('visits.id'), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500))
    file_size = db.Column(db.Integer)
    mime_type = db.Column(db.String(100))
    file_data = db.Column(db.LargeBinary)
    uploaded_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    def to_dict(self, include_data=False):
        result = {
            'id': self.id,
            'visit_id': self.visit_id,
            'file_name': self.file_name,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'mime_type': self.mime_type,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None
        }
        
        if include_data and self.file_data:
            import base64
            result['file_data'] = base64.b64encode(self.file_data).decode('utf-8')
            
        return result