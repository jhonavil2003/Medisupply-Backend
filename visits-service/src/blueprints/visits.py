from flask import Blueprint, request, jsonify
from src.entities.visit import Visit
from src.entities.salesperson import Salesperson
from src.entities.visit_status import VisitStatus
from src.session import db

visits_bp = Blueprint('visits', __name__, url_prefix='/api/visits')


@visits_bp.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'visits-service'}), 200


@visits_bp.route('/salespersons', methods=['GET'])
def get_salespersons():
    """Obtener lista de vendedores"""
    try:
        salespersons = Salesperson.query.filter_by(is_active=True).all()
        return jsonify({
            'salespersons': [sp.to_dict() for sp in salespersons]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@visits_bp.route('', methods=['GET'])
def get_visits():
    """Obtener lista de visitas"""
    try:
        visits = Visit.query.limit(50).all()
        return jsonify({
            'visits': [visit.to_dict() for visit in visits]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@visits_bp.route('', methods=['POST'])
def create_visit():
    """Crear una nueva visita"""
    try:
        data = request.get_json()
        
        # Validaciones básicas
        if not data.get('customer_id') or not data.get('salesperson_id'):
            return jsonify({'error': 'customer_id y salesperson_id son requeridos'}), 400
            
        if not data.get('visit_date') or not data.get('visit_time'):
            return jsonify({'error': 'visit_date y visit_time son requeridos'}), 400
        
        # Crear visita
        visit = Visit(
            customer_id=data['customer_id'],
            salesperson_id=data['salesperson_id'],
            visit_date=data['visit_date'],
            visit_time=data['visit_time'],
            contacted_persons=data.get('contacted_persons'),
            clinical_findings=data.get('clinical_findings'),
            additional_notes=data.get('additional_notes'),
            address=data.get('address'),
            latitude=data.get('latitude'),
            longitude=data.get('longitude'),
            status=VisitStatus.SCHEDULED
        )
        
        db.session.add(visit)
        db.session.commit()
        
        return jsonify({
            'message': 'Visita creada exitosamente',
            'visit': visit.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@visits_bp.route('/<int:visit_id>', methods=['GET'])
def get_visit(visit_id):
    """Obtener una visita por ID"""
    try:
        visit = Visit.query.get_or_404(visit_id)
        return jsonify({
            'visit': visit.to_dict(include_files=True)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500