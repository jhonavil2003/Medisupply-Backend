"""
Blueprint para gestión de visitas
Endpoints CRUD para visitas a clientes
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, date, time
from src.entities.visit import Visit
from src.entities.salesperson import Salesperson
from src.models.customer import Customer
from src.entities.visit_status import VisitStatus
from src.session import db
from sqlalchemy.exc import NoResultFound
from sqlalchemy import and_, or_

visits_bp = Blueprint('visits', __name__, url_prefix='/api/visits')


@visits_bp.route('', methods=['POST'])
def create_visit():
    """Crear una nueva visita"""
    try:
        data = request.get_json()
        
        # Validar campos requeridos
        required_fields = ['customer_id', 'salesperson_id', 'visit_date', 'visit_time']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Campo requerido: {field}'}), 400
        
        # Validar que customer existe
        customer = Customer.query.get(data['customer_id'])
        if not customer:
            return jsonify({'error': 'Cliente no encontrado'}), 404
        
        # Validar que salesperson existe  
        salesperson = Salesperson.query.get(data['salesperson_id'])
        if not salesperson:
            return jsonify({'error': 'Vendedor no encontrado'}), 404
        
        # Parsear fecha y hora
        try:
            visit_date = datetime.strptime(data['visit_date'], '%Y-%m-%d').date()
            visit_time = datetime.strptime(data['visit_time'], '%H:%M').time()
        except ValueError as e:
            return jsonify({'error': f'Formato de fecha/hora inválido: {str(e)}'}), 400
        
        # Crear nueva visita
        visit = Visit(
            customer_id=data['customer_id'],
            salesperson_id=data['salesperson_id'],
            visit_date=visit_date,
            visit_time=visit_time,
            contacted_persons=data.get('contacted_persons'),
            clinical_findings=data.get('clinical_findings'),
            additional_notes=data.get('additional_notes'),
            address=data.get('address'),
            latitude=data.get('latitude'),
            longitude=data.get('longitude'),
            status=VisitStatus(data.get('status', 'SCHEDULED'))
        )
        
        db.session.add(visit)
        db.session.commit()
        
        return jsonify({
            'message': 'Visita creada exitosamente',
            'visit': visit.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al crear visita: {str(e)}'}), 500


@visits_bp.route('', methods=['GET'])
def get_visits():
    """Obtener lista de visitas con filtros opcionales"""
    try:
        # Parámetros de consulta
        customer_id = request.args.get('customer_id', type=int)
        salesperson_id = request.args.get('salesperson_id', type=int)
        status = request.args.get('status')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
        # Construir query
        query = Visit.query
        
        # Aplicar filtros
        if customer_id:
            query = query.filter(Visit.customer_id == customer_id)
        if salesperson_id:
            query = query.filter(Visit.salesperson_id == salesperson_id)
        if status:
            query = query.filter(Visit.status == VisitStatus(status))
        if date_from:
            date_from_parsed = datetime.strptime(date_from, '%Y-%m-%d').date()
            query = query.filter(Visit.visit_date >= date_from_parsed)
        if date_to:
            date_to_parsed = datetime.strptime(date_to, '%Y-%m-%d').date()
            query = query.filter(Visit.visit_date <= date_to_parsed)
        
        # Ordenar por fecha
        visits = query.order_by(Visit.visit_date.desc(), Visit.visit_time.desc()).all()
        
        return jsonify({
            'visits': [visit.to_dict() for visit in visits],
            'total': len(visits)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error al obtener visitas: {str(e)}'}), 500


@visits_bp.route('/<int:visit_id>', methods=['GET'])
def get_visit_by_id(visit_id):
    """Obtener una visita por ID"""
    try:
        visit = Visit.query.get(visit_id)
        if not visit:
            return jsonify({'error': 'Visita no encontrada'}), 404
        
        return jsonify(visit.to_dict(include_files=True)), 200
        
    except Exception as e:
        return jsonify({'error': f'Error al obtener visita: {str(e)}'}), 500


@visits_bp.route('/<int:visit_id>', methods=['PUT'])
def update_visit(visit_id):
    """Actualizar una visita existente"""
    try:
        visit = Visit.query.get(visit_id)
        if not visit:
            return jsonify({'error': 'Visita no encontrada'}), 404
        
        data = request.get_json()
        
        # Actualizar campos si están presentes
        if 'customer_id' in data:
            customer = Customer.query.get(data['customer_id'])
            if not customer:
                return jsonify({'error': 'Cliente no encontrado'}), 404
            visit.customer_id = data['customer_id']
        
        if 'salesperson_id' in data:
            salesperson = Salesperson.query.get(data['salesperson_id'])
            if not salesperson:
                return jsonify({'error': 'Vendedor no encontrado'}), 404
            visit.salesperson_id = data['salesperson_id']
        
        if 'visit_date' in data:
            try:
                visit.visit_date = datetime.strptime(data['visit_date'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': 'Formato de fecha inválido'}), 400
        
        if 'visit_time' in data:
            try:
                visit.visit_time = datetime.strptime(data['visit_time'], '%H:%M').time()
            except ValueError:
                return jsonify({'error': 'Formato de hora inválido'}), 400
        
        if 'contacted_persons' in data:
            visit.contacted_persons = data['contacted_persons']
        if 'clinical_findings' in data:
            visit.clinical_findings = data['clinical_findings']
        if 'additional_notes' in data:
            visit.additional_notes = data['additional_notes']
        if 'address' in data:
            visit.address = data['address']
        if 'latitude' in data:
            visit.latitude = data['latitude']
        if 'longitude' in data:
            visit.longitude = data['longitude']
        if 'status' in data:
            visit.status = VisitStatus(data['status'])
        
        visit.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Visita actualizada exitosamente',
            'visit': visit.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al actualizar visita: {str(e)}'}), 500


@visits_bp.route('/<int:visit_id>', methods=['DELETE'])
def delete_visit(visit_id):
    """Eliminar una visita"""
    try:
        visit = Visit.query.get(visit_id)
        if not visit:
            return jsonify({'error': 'Visita no encontrada'}), 404
        
        db.session.delete(visit)
        db.session.commit()
        
        return jsonify({
            'message': 'Visita eliminada exitosamente'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al eliminar visita: {str(e)}'}), 500


@visits_bp.route('/salesperson/<int:salesperson_id>', methods=['GET'])
def get_visits_by_salesperson(salesperson_id):
    """Obtener visitas por vendedor"""
    try:
        # Validar que el vendedor existe
        salesperson = Salesperson.query.get(salesperson_id)
        if not salesperson:
            return jsonify({'error': 'Vendedor no encontrado'}), 404
        
        visits = Visit.query.filter_by(salesperson_id=salesperson_id).all()
        
        return jsonify({
            'salesperson': salesperson.to_dict(),
            'visits': [visit.to_dict() for visit in visits],
            'total': len(visits)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error al obtener visitas: {str(e)}'}), 500


@visits_bp.route('/customer/<int:customer_id>', methods=['GET'])
def get_visits_by_customer(customer_id):
    """Obtener visitas por cliente"""
    try:
        # Validar que el cliente existe
        customer = Customer.query.get(customer_id)
        if not customer:
            return jsonify({'error': 'Cliente no encontrado'}), 404
        
        visits = Visit.query.filter_by(customer_id=customer_id).all()
        
        return jsonify({
            'customer': customer.to_dict(),
            'visits': [visit.to_dict() for visit in visits],
            'total': len(visits)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error al obtener visitas: {str(e)}'}), 500


@visits_bp.route('/status/<status>', methods=['GET'])
def get_visits_by_status(status):
    """Obtener visitas por estado"""
    try:
        try:
            status_enum = VisitStatus(status.upper())
        except ValueError:
            return jsonify({'error': 'Estado de visita inválido'}), 400
        
        visits = Visit.query.filter_by(status=status_enum).all()
        
        return jsonify({
            'status': status.upper(),
            'visits': [visit.to_dict() for visit in visits],
            'total': len(visits)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error al obtener visitas: {str(e)}'}), 500