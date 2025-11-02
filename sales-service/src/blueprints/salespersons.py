"""
Blueprint para gestión de vendedores
Endpoints CRUD para vendedores
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
from src.entities.salesperson import Salesperson
from src.session import db

salespersons_bp = Blueprint('salespersons', __name__, url_prefix='/salespersons')


@salespersons_bp.route('/', methods=['POST'])
def create_salesperson():
    """Crear un nuevo vendedor"""
    try:
        data = request.get_json()
        
        # Validar campos requeridos
        required_fields = ['employee_id', 'first_name', 'last_name', 'email']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Campo requerido: {field}'}), 400
        
        # Verificar que employee_id no exista
        existing = Salesperson.query.filter_by(employee_id=data['employee_id']).first()
        if existing:
            return jsonify({'error': 'Ya existe un vendedor con ese employee_id'}), 400
        
        # Verificar que email no exista
        existing_email = Salesperson.query.filter_by(email=data['email']).first()
        if existing_email:
            return jsonify({'error': 'Ya existe un vendedor con ese email'}), 400
        
        # Parsear fecha de contratación si se proporciona
        hire_date = None
        if 'hire_date' in data and data['hire_date']:
            try:
                hire_date = datetime.strptime(data['hire_date'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': 'Formato de fecha de contratación inválido (YYYY-MM-DD)'}), 400
        
        # Crear nuevo vendedor
        salesperson = Salesperson(
            employee_id=data['employee_id'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            email=data['email'],
            phone=data.get('phone'),
            territory=data.get('territory'),
            hire_date=hire_date,
            is_active=data.get('is_active', True)
        )
        
        db.session.add(salesperson)
        db.session.commit()
        
        return jsonify({
            'message': 'Vendedor creado exitosamente',
            'salesperson': salesperson.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al crear vendedor: {str(e)}'}), 500


@salespersons_bp.route('/', methods=['GET'])
def get_salespersons():
    """Obtener lista de vendedores con filtros opcionales"""
    try:
        # Parámetros de consulta
        territory = request.args.get('territory')
        is_active = request.args.get('is_active')
        
        # Construir query
        query = Salesperson.query
        
        # Aplicar filtros
        if territory:
            query = query.filter(Salesperson.territory == territory)
        if is_active is not None:
            is_active_bool = is_active.lower() in ['true', '1', 'yes']
            query = query.filter(Salesperson.is_active == is_active_bool)
        
        # Ordenar por nombre
        salespersons = query.order_by(Salesperson.first_name, Salesperson.last_name).all()
        
        return jsonify({
            'salespersons': [sp.to_dict() for sp in salespersons],
            'total': len(salespersons)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error al obtener vendedores: {str(e)}'}), 500


@salespersons_bp.route('/<int:salesperson_id>', methods=['GET'])
def get_salesperson_by_id(salesperson_id):
    """Obtener un vendedor por ID"""
    try:
        salesperson = Salesperson.query.get(salesperson_id)
        if not salesperson:
            return jsonify({'error': 'Vendedor no encontrado'}), 404
        
        return jsonify(salesperson.to_dict(include_visits=True)), 200
        
    except Exception as e:
        return jsonify({'error': f'Error al obtener vendedor: {str(e)}'}), 500


@salespersons_bp.route('/<int:salesperson_id>', methods=['PUT'])
def update_salesperson(salesperson_id):
    """Actualizar un vendedor existente"""
    try:
        salesperson = Salesperson.query.get(salesperson_id)
        if not salesperson:
            return jsonify({'error': 'Vendedor no encontrado'}), 404
        
        data = request.get_json()
        
        # Actualizar campos si están presentes
        if 'employee_id' in data:
            # Verificar que no exista otro vendedor con el mismo employee_id
            existing = Salesperson.query.filter(
                Salesperson.employee_id == data['employee_id'],
                Salesperson.id != salesperson_id
            ).first()
            if existing:
                return jsonify({'error': 'Ya existe otro vendedor con ese employee_id'}), 400
            salesperson.employee_id = data['employee_id']
        
        if 'email' in data:
            # Verificar que no exista otro vendedor con el mismo email
            existing = Salesperson.query.filter(
                Salesperson.email == data['email'],
                Salesperson.id != salesperson_id
            ).first()
            if existing:
                return jsonify({'error': 'Ya existe otro vendedor con ese email'}), 400
            salesperson.email = data['email']
        
        if 'first_name' in data:
            salesperson.first_name = data['first_name']
        if 'last_name' in data:
            salesperson.last_name = data['last_name']
        if 'phone' in data:
            salesperson.phone = data['phone']
        if 'territory' in data:
            salesperson.territory = data['territory']
        if 'is_active' in data:
            salesperson.is_active = data['is_active']
        
        if 'hire_date' in data:
            if data['hire_date']:
                try:
                    salesperson.hire_date = datetime.strptime(data['hire_date'], '%Y-%m-%d').date()
                except ValueError:
                    return jsonify({'error': 'Formato de fecha de contratación inválido'}), 400
            else:
                salesperson.hire_date = None
        
        salesperson.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Vendedor actualizado exitosamente',
            'salesperson': salesperson.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al actualizar vendedor: {str(e)}'}), 500


@salespersons_bp.route('/<int:salesperson_id>', methods=['DELETE'])
def delete_salesperson(salesperson_id):
    """Eliminar un vendedor (soft delete - marcar como inactivo)"""
    try:
        salesperson = Salesperson.query.get(salesperson_id)
        if not salesperson:
            return jsonify({'error': 'Vendedor no encontrado'}), 404
        
        # Verificar si tiene visitas asociadas
        from src.entities.visit import Visit
        visits = Visit.query.filter_by(salesperson_id=salesperson_id).first()
        if visits:
            return jsonify({
                'error': 'No se puede eliminar el vendedor porque tiene visitas asociadas'
            }), 400
        else:
            # Hard delete si no tiene visitas
            db.session.delete(salesperson)
            db.session.commit()
            
            return jsonify({
                'message': 'Vendedor eliminado exitosamente'
            }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al eliminar vendedor: {str(e)}'}), 500


@salespersons_bp.route('/employee/<employee_id>', methods=['GET'])
def get_salesperson_by_employee_id(employee_id):
    """Obtener un vendedor por employee_id"""
    try:
        salesperson = Salesperson.query.filter_by(employee_id=employee_id).first()
        if not salesperson:
            return jsonify({'error': 'Vendedor no encontrado'}), 404
        
        return jsonify(salesperson.to_dict()), 200
        
    except Exception as e:
        return jsonify({'error': f'Error al obtener vendedor: {str(e)}'}), 500


@salespersons_bp.route('/territory/<territory>', methods=['GET'])
def get_salespersons_by_territory(territory):
    """Obtener vendedores por territorio"""
    try:
        salespersons = Salesperson.query.filter_by(territory=territory, is_active=True).all()
        
        return jsonify({
            'territory': territory,
            'salespersons': [sp.to_dict() for sp in salespersons],
            'total': len(salespersons)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error al obtener vendedores: {str(e)}'}), 500