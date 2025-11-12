"""
Blueprint para carga masiva de suppliers mediante archivos CSV.
Endpoints para upload, tracking de progreso y descarga de errores.
"""
from flask import Blueprint, request, jsonify, current_app, send_file
from werkzeug.utils import secure_filename
import io
import csv
from src.session import db
from src.models.bulk_upload_supplier_job import BulkUploadSupplierJob, JobStatus
from src.commands.validate_supplier_csv import ValidateSupplierCSV
from src.commands.process_suppliers_bulk import ProcessSuppliersBulk
from src.errors.errors import ApiError

bulk_upload_suppliers_bp = Blueprint('bulk_upload_suppliers', __name__, url_prefix='/api/suppliers')


@bulk_upload_suppliers_bp.route('/bulk-upload', methods=['POST'])
def upload_suppliers_csv():
    """
    Endpoint para cargar archivo CSV de suppliers.
    Valida el archivo y crea un job para procesamiento en background.
    """
    try:
        # Validar que se envió un archivo
        if 'file' not in request.files:
            raise ApiError('No se envió ningún archivo', 400)
        
        file = request.files['file']
        
        if file.filename == '':
            raise ApiError('Nombre de archivo vacío', 400)
        
        # Leer contenido del archivo
        file_content = file.read()
        filename = secure_filename(file.filename)
        file_size = len(file_content)
        
        # Fase 1: Validación rápida de estructura
        validator = ValidateSupplierCSV()
        is_valid, errors, total_rows = validator.validate_file_structure(file_content, filename)
        
        if not is_valid:
            return jsonify({
                'error': 'Validación de estructura fallida',
                'details': errors
            }), 400
        
        # Parsear CSV a lista
        csv_data = validator.parse_csv_to_list(file_content)
        
        # Crear job para procesamiento
        job = BulkUploadSupplierJob(
            filename=filename,
            total_rows=total_rows,
            file_size_bytes=file_size
        )
        db.session.add(job)
        db.session.commit()
        
        # Iniciar procesamiento en background
        processor = ProcessSuppliersBulk(current_app._get_current_object())
        processor.start_processing(job.job_id, csv_data)
        
        return jsonify({
            'message': 'Archivo recibido y en procesamiento',
            'job_id': job.job_id,
            'filename': filename,
            'total_rows': total_rows,
            'warnings': validator.warnings
        }), 202
        
    except ApiError as e:
        raise e
    except Exception as e:
        current_app.logger.error(f"Error en upload_suppliers_csv: {str(e)}")
        raise ApiError(f'Error al procesar archivo: {str(e)}', 500)


@bulk_upload_suppliers_bp.route('/bulk-upload/jobs/<job_id>', methods=['GET'])
def get_job_status(job_id):
    """
    Obtiene el estado actual de un job de carga masiva.
    """
    try:
        job = BulkUploadSupplierJob.query.filter_by(job_id=job_id).first()
        
        if not job:
            raise ApiError('Job no encontrado', 404)
        
        return jsonify(job.to_dict()), 200
        
    except ApiError as e:
        raise e
    except Exception as e:
        current_app.logger.error(f"Error en get_job_status: {str(e)}")
        raise ApiError('Error al obtener estado del job', 500)


@bulk_upload_suppliers_bp.route('/bulk-upload/jobs/<job_id>/errors', methods=['GET'])
def download_errors(job_id):
    """
    Descarga un archivo CSV con los errores del job.
    """
    try:
        job = BulkUploadSupplierJob.query.filter_by(job_id=job_id).first()
        
        if not job:
            raise ApiError('Job no encontrado', 404)
        
        errors = job.get_errors()
        
        if not errors:
            raise ApiError('No hay errores para este job', 404)
        
        # Crear CSV en memoria
        output = io.StringIO()
        
        # Obtener todas las claves de los datos
        if errors:
            all_keys = set()
            for error in errors:
                if 'data' in error:
                    all_keys.update(error['data'].keys())
            
            fieldnames = ['row_number', 'error_message'] + sorted(list(all_keys))
            
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            
            for error in errors:
                row = {
                    'row_number': error.get('row', ''),
                    'error_message': error.get('error', '')
                }
                row.update(error.get('data', {}))
                writer.writerow(row)
        
        # Convertir a bytes
        output.seek(0)
        bytes_output = io.BytesIO(output.getvalue().encode('utf-8-sig'))
        bytes_output.seek(0)
        
        return send_file(
            bytes_output,
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'errors_{job_id}.csv'
        )
        
    except ApiError as e:
        raise e
    except Exception as e:
        current_app.logger.error(f"Error en download_errors: {str(e)}")
        raise ApiError('Error al descargar errores', 500)


@bulk_upload_suppliers_bp.route('/bulk-upload/jobs', methods=['GET'])
def get_upload_history():
    """
    Obtiene el historial de jobs de carga masiva.
    Soporta paginación y filtros.
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status_filter = request.args.get('status', None)
        
        # Validar parámetros
        if page < 1:
            raise ApiError('Página debe ser mayor a 0', 400)
        if per_page < 1 or per_page > 100:
            raise ApiError('per_page debe estar entre 1 y 100', 400)
        
        # Query base
        query = BulkUploadSupplierJob.query
        
        # Aplicar filtro de estado si existe
        if status_filter:
            if status_filter not in [s.value for s in JobStatus]:
                raise ApiError(f'Estado inválido. Valores permitidos: {[s.value for s in JobStatus]}', 400)
            query = query.filter_by(status=status_filter)
        
        # Ordenar por fecha de creación descendente
        query = query.order_by(BulkUploadSupplierJob.created_at.desc())
        
        # Paginar
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'jobs': [job.to_dict() for job in pagination.items],
            'pagination': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total_pages': pagination.pages,
                'total_items': pagination.total
            }
        }), 200
        
    except ApiError as e:
        raise e
    except Exception as e:
        current_app.logger.error(f"Error en get_upload_history: {str(e)}")
        raise ApiError('Error al obtener historial', 500)


@bulk_upload_suppliers_bp.route('/bulk-upload/stats', methods=['GET'])
def get_upload_stats():
    """
    Obtiene estadísticas generales de cargas masivas.
    """
    try:
        total_jobs = BulkUploadSupplierJob.query.count()
        completed_jobs = BulkUploadSupplierJob.query.filter_by(status=JobStatus.COMPLETED).count()
        failed_jobs = BulkUploadSupplierJob.query.filter_by(status=JobStatus.FAILED).count()
        processing_jobs = BulkUploadSupplierJob.query.filter_by(status=JobStatus.PROCESSING).count()
        pending_jobs = BulkUploadSupplierJob.query.filter_by(status=JobStatus.PENDING).count()
        
        # Calcular total de filas procesadas
        completed_jobs_list = BulkUploadSupplierJob.query.filter_by(status=JobStatus.COMPLETED).all()
        total_suppliers_created = sum(job.get_successful_rows() for job in completed_jobs_list)
        total_rows_failed = sum(job.get_failed_rows() for job in completed_jobs_list)
        
        return jsonify({
            'total_jobs': total_jobs,
            'jobs_by_status': {
                'completed': completed_jobs,
                'failed': failed_jobs,
                'processing': processing_jobs,
                'pending': pending_jobs
            },
            'total_suppliers_created': total_suppliers_created,
            'total_rows_failed': total_rows_failed
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error en get_upload_stats: {str(e)}")
        raise ApiError('Error al obtener estadísticas', 500)


@bulk_upload_suppliers_bp.route('/bulk-upload/jobs/<job_id>/cancel', methods=['POST'])
def cancel_job(job_id):
    """
    Cancela un job de carga masiva.
    Solo se pueden cancelar jobs en estado PENDING o PROCESSING.
    """
    try:
        job = BulkUploadSupplierJob.query.filter_by(job_id=job_id).first()
        
        if not job:
            raise ApiError('Job no encontrado', 404)
        
        if job.status not in [JobStatus.PENDING, JobStatus.PROCESSING]:
            raise ApiError(f'No se puede cancelar un job en estado {job.status}', 400)
        
        job.set_status(JobStatus.CANCELLED)
        db.session.commit()
        
        return jsonify({
            'message': 'Job cancelado exitosamente',
            'job_id': job.job_id,
            'status': job.status
        }), 200
        
    except ApiError as e:
        raise e
    except Exception as e:
        current_app.logger.error(f"Error en cancel_job: {str(e)}")
        raise ApiError('Error al cancelar job', 500)


@bulk_upload_suppliers_bp.route('/bulk-upload/template', methods=['GET'])
def download_template():
    """
    Descarga plantilla CSV con ejemplos de suppliers.
    Incluye todas las columnas requeridas y opcionales con 3 ejemplos.
    """
    try:
        # Crear CSV en memoria
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Headers (todas las columnas)
        headers = [
            'tax_id', 'name', 'legal_name', 'address_line1', 'address_line2',
            'city', 'state', 'postal_code', 'country', 'phone', 'email',
            'website', 'payment_terms', 'credit_limit', 'currency',
            'is_certified', 'certification_date', 'certification_expiry', 'is_active'
        ]
        writer.writerow(headers)
        
        # Ejemplo 1: Supplier con todos los campos
        writer.writerow([
            '900123456789',  # tax_id
            'Distribuidora Médica Premium',  # name
            'Distribuidora Médica Premium S.A.S.',  # legal_name
            'Calle 100 # 15-45',  # address_line1
            'Edificio Medical Center, Piso 5',  # address_line2
            'Bogotá',  # city
            'Cundinamarca',  # state
            '110111',  # postal_code
            'Colombia',  # country
            '+57-1-6001234',  # phone
            'contacto@distmedpremium.com',  # email
            'https://distmedpremium.com',  # website
            'Net 30',  # payment_terms
            '100000.00',  # credit_limit
            'COP',  # currency
            'true',  # is_certified
            '2024-01-15',  # certification_date
            '2026-01-15',  # certification_expiry
            'true'  # is_active
        ])
        
        # Ejemplo 2: Supplier con campos mínimos requeridos
        writer.writerow([
            '800234567890',  # tax_id
            'Suministros Hospitalarios Norte',  # name
            '',  # legal_name (opcional)
            'Carrera 45 # 123-45',  # address_line1
            '',  # address_line2 (opcional)
            'Medellín',  # city (opcional pero recomendado)
            'Antioquia',  # state (opcional)
            '',  # postal_code (opcional)
            'Colombia',  # country
            '+57-4-3002345',  # phone
            'ventas@sumihospnorte.com',  # email
            '',  # website (opcional)
            '',  # payment_terms (opcional)
            '',  # credit_limit (opcional)
            'USD',  # currency (opcional)
            'false',  # is_certified (opcional)
            '',  # certification_date (opcional)
            '',  # certification_expiry (opcional)
            'true'  # is_active (opcional)
        ])
        
        # Ejemplo 3: Supplier internacional certificado
        writer.writerow([
            'RFC-ABC123456',  # tax_id
            'MedEquip Internacional',  # name
            'MedEquip Internacional S.A. de C.V.',  # legal_name
            'Avenida Reforma 250',  # address_line1
            'Colonia Juárez',  # address_line2
            'Ciudad de México',  # city
            'CDMX',  # state
            '06600',  # postal_code
            'México',  # country
            '+52-55-12345678',  # phone
            'mexico@medequip.com',  # email
            'https://medequip.mx',  # website
            'Net 45',  # payment_terms
            '75000.00',  # credit_limit
            'USD',  # currency
            'true',  # is_certified
            '2023-06-01',  # certification_date
            '2025-06-01',  # certification_expiry
            'true'  # is_active
        ])
        
        # Convertir a bytes
        output.seek(0)
        csv_bytes = io.BytesIO(output.getvalue().encode('utf-8'))
        
        return send_file(
            csv_bytes,
            mimetype='text/csv',
            as_attachment=True,
            download_name='plantilla_suppliers.csv'
        )
        
    except Exception as e:
        current_app.logger.error(f"Error en download_template: {str(e)}")
        raise ApiError('Error al generar plantilla', 500)
