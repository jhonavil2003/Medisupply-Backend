"""
Blueprint para carga masiva de productos desde archivos CSV.
Proporciona endpoints para subir, procesar y monitorear jobs de carga masiva.
"""
from flask import Blueprint, request, jsonify, send_file, current_app
from werkzeug.utils import secure_filename
import hashlib
import csv
import io
from datetime import datetime
from src.session import db
from src.models.bulk_upload_job import BulkUploadJob, JobStatus
from src.commands.validate_product_csv import ValidateProductCSV
from src.commands.process_products_bulk import ProcessProductsBulk
from src.errors.errors import ApiError


bulk_upload_bp = Blueprint('bulk_upload', __name__, url_prefix='/api/products/bulk-upload')


@bulk_upload_bp.route('/template', methods=['GET'])
def download_template():
    """
    GET /api/products/bulk-upload/template
    
    Descarga una plantilla CSV con las columnas requeridas y ejemplos.
    
    Returns:
        Archivo CSV con headers y filas de ejemplo
    """
    try:
        # Crear CSV en memoria
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Headers
        headers = [
            'sku', 'name', 'description', 'category', 'subcategory',
            'unit_price', 'currency', 'unit_of_measure', 'supplier_id',
            'requires_cold_chain', 'storage_temperature_min', 'storage_temperature_max', 'storage_humidity_max',
            'sanitary_registration', 'requires_prescription', 'regulatory_class',
            'weight_kg', 'length_cm', 'width_cm', 'height_cm',
            'manufacturer', 'country_of_origin', 'barcode', 'image_url',
            'is_active', 'is_discontinued'
        ]
        writer.writerow(headers)
        
        # Fila de ejemplo 1: Producto con cadena de frío
        writer.writerow([
            'VAC-FLU-2025',
            'Vacuna Influenza Estacional 2025',
            'Vacuna contra la influenza, dosis única, vial de 0.5ml',
            'Medicamentos',
            'Vacunas',
            '15.50',
            'USD',
            'vial',
            '1',
            'true',
            '2',
            '8',
            '60',  # storage_humidity_max
            'INVIMA-2025-1234',
            'true',
            'Clase III',
            '0.050',
            '',
            '',
            '',
            'PharmaCorp International',
            'USA',
            '7501234567899',
            'https://example.com/images/vac-flu-2025.jpg',  # image_url
            'true',
            'false'  # is_discontinued
        ])
        
        # Fila de ejemplo 2: Equipo médico
        writer.writerow([
            'STET-DIG-PRO',
            'Estetoscopio Digital Profesional',
            'Estetoscopio digital con amplificación de sonido y grabación',
            'Equipos Médicos',
            'Diagnóstico',
            '180.00',
            'USD',
            'unidad',
            '2',
            'false',
            '',
            '',
            '',  # storage_humidity_max
            'CE-2024-5678',
            'false',
            'Clase IIa',
            '0.250',
            '25',
            '8',
            '5',
            'MedTech Devices Ltd',
            'Germany',
            '7502345678901',
            '',  # image_url
            'true',
            'false'  # is_discontinued
        ])
        
        # Fila de ejemplo 3: Material de curación
        writer.writerow([
            'GASA-EST-10X10',
            'Gasa estéril 10x10cm',
            'Gasa estéril de algodón, paquete x 10 unidades',
            'Instrumental',
            'Material de curación',
            '2.50',
            'USD',
            'paquete',
            '1',
            'false',
            '',
            '',
            '',  # storage_humidity_max
            'INVIMA-2024-9012',
            'false',
            'Clase I',
            '0.035',
            '',
            '',
            '',
            'MedSupply Colombia',
            'Colombia',
            '7503456789012',
            '',  # image_url
            'true',
            'false'  # is_discontinued
        ])
        
        # Convertir a bytes
        output.seek(0)
        file_bytes = io.BytesIO(output.getvalue().encode('utf-8-sig'))  # UTF-8 with BOM for Excel
        file_bytes.seek(0)
        
        return send_file(
            file_bytes,
            mimetype='text/csv',
            as_attachment=True,
            download_name='plantilla_productos.csv'
        )
        
    except Exception as e:
        raise ApiError(f"Error generando plantilla: {str(e)}", 500)


@bulk_upload_bp.route('', methods=['POST'])
def upload_csv():
    """
    POST /api/products/bulk-upload
    
    Sube un archivo CSV y crea un job de procesamiento en background.
    
    Request:
        - file: Archivo CSV (multipart/form-data)
        - created_by: Usuario que crea el job (opcional)
    
    Returns:
        {
            "job_id": "uuid",
            "status": "pending",
            "filename": "productos.csv",
            "total_rows": 150,
            "message": "Archivo recibido, procesamiento iniciado"
        }
    """
    try:
        # Validar que se envió un archivo
        if 'file' not in request.files:
            raise ApiError('No se envió ningún archivo. Use el campo "file"', 400)
        
        file = request.files['file']
        
        if file.filename == '':
            raise ApiError('Archivo sin nombre', 400)
        
        # Obtener metadata opcional
        created_by = request.form.get('created_by', 'anonymous')
        
        # Leer contenido del archivo
        file_content = file.read()
        file.seek(0)  # Reset para poder leer de nuevo si es necesario
        
        filename = secure_filename(file.filename)
        
        # Calcular hash del archivo
        file_hash = hashlib.sha256(file_content).hexdigest()
        
        # Verificar si ya existe un job con este hash
        existing_job = BulkUploadJob.query.filter_by(file_hash=file_hash).first()
        if existing_job and existing_job.status in [JobStatus.PENDING, JobStatus.PROCESSING]:
            return jsonify({
                'warning': 'Este archivo ya está siendo procesado',
                'existing_job': existing_job.to_dict()
            }), 200
        
        # Fase 1: Validación rápida de estructura
        validator = ValidateProductCSV()
        is_valid, errors, total_rows = validator.validate_file_structure(file_content, filename)
        
        if not is_valid:
            raise ApiError(f"Archivo CSV inválido: {'; '.join(errors)}", 400)
        
        # Crear job de procesamiento
        job = BulkUploadJob(
            filename=filename,
            total_rows=total_rows,
            created_by=created_by,
            file_size_bytes=len(file_content),
            file_hash=file_hash
        )
        
        db.session.add(job)
        db.session.commit()
        
        # Parsear CSV a lista de diccionarios
        csv_data = validator.parse_csv_to_list(file_content)
        
        # Iniciar procesamiento en background
        processor = ProcessProductsBulk(current_app._get_current_object())
        processor.start_processing(job.job_id, csv_data)
        
        return jsonify({
            'job_id': job.job_id,
            'status': job.status,
            'filename': job.filename,
            'total_rows': job.total_rows,
            'message': f'Archivo recibido correctamente. Procesando {total_rows} productos en background.'
        }), 202  # 202 Accepted
        
    except ApiError:
        raise
    except Exception as e:
        raise ApiError(f"Error al procesar la carga: {str(e)}", 500)


@bulk_upload_bp.route('/<job_id>', methods=['GET'])
def get_job_status(job_id):
    """
    GET /api/products/bulk-upload/{job_id}
    
    Obtiene el estado actual de un job de carga masiva.
    
    Query params:
        - include_errors: true/false (incluir lista de errores en la respuesta)
    
    Returns:
        {
            "job_id": "uuid",
            "status": "processing",
            "total_rows": 150,
            "processed_rows": 75,
            "successful_rows": 70,
            "failed_rows": 5,
            "progress_percentage": 50.0,
            "success_rate": 93.33,
            ...
        }
    """
    try:
        job = BulkUploadJob.query.filter_by(job_id=job_id).first()
        
        if not job:
            raise ApiError(f"Job {job_id} no encontrado", 404)
        
        include_errors = request.args.get('include_errors', 'false').lower() == 'true'
        
        return jsonify(job.to_dict(include_errors=include_errors)), 200
        
    except ApiError:
        raise
    except Exception as e:
        raise ApiError(f"Error al obtener estado del job: {str(e)}", 500)


@bulk_upload_bp.route('/history', methods=['GET'])
def get_upload_history():
    """
    GET /api/products/bulk-upload/history
    
    Lista el historial de cargas masivas.
    
    Query params:
        - status: Filtrar por estado (pending, processing, completed, failed)
        - created_by: Filtrar por usuario
        - limit: Número de registros (default: 50)
        - offset: Paginación (default: 0)
    
    Returns:
        {
            "jobs": [...],
            "total": 125,
            "limit": 50,
            "offset": 0
        }
    """
    try:
        # Parámetros de filtrado
        status = request.args.get('status')
        created_by = request.args.get('created_by')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        # Validar límite
        if limit > 100:
            limit = 100
        
        # Query base
        query = BulkUploadJob.query
        
        # Aplicar filtros
        if status:
            query = query.filter_by(status=status)
        
        if created_by:
            query = query.filter_by(created_by=created_by)
        
        # Total de registros
        total = query.count()
        
        # Obtener resultados paginados
        jobs = query.order_by(BulkUploadJob.created_at.desc())\
                    .limit(limit)\
                    .offset(offset)\
                    .all()
        
        return jsonify({
            'jobs': [job.to_summary_dict() for job in jobs],
            'total': total,
            'limit': limit,
            'offset': offset
        }), 200
        
    except ValueError as e:
        raise ApiError('Parámetros inválidos: limit y offset deben ser números', 400)
    except Exception as e:
        raise ApiError(f"Error al obtener historial: {str(e)}", 500)


@bulk_upload_bp.route('/<job_id>/errors', methods=['GET'])
def download_errors(job_id):
    """
    GET /api/products/bulk-upload/{job_id}/errors
    
    Descarga un CSV con las filas que fallaron y sus errores.
    
    Returns:
        Archivo CSV con las filas fallidas y mensajes de error
    """
    try:
        job = BulkUploadJob.query.filter_by(job_id=job_id).first()
        
        if not job:
            raise ApiError(f"Job {job_id} no encontrado", 404)
        
        errors = job.get_errors()
        
        if not errors:
            raise ApiError('Este job no tiene errores', 404)
        
        # Crear CSV en memoria
        output = io.StringIO()
        
        if errors:
            # Obtener headers del primer error
            first_error = errors[0]
            if 'data' in first_error and first_error['data']:
                headers = ['row_number', 'error_message'] + list(first_error['data'].keys())
            else:
                headers = ['row_number', 'error_message']
            
            writer = csv.writer(output)
            writer.writerow(headers)
            
            # Escribir errores
            for error in errors:
                row_data = error.get('data', {})
                row = [
                    error.get('row', ''),
                    error.get('error', '')
                ] + [row_data.get(h, '') for h in headers[2:]]
                writer.writerow(row)
        
        # Convertir a bytes
        output.seek(0)
        file_bytes = io.BytesIO(output.getvalue().encode('utf-8-sig'))
        file_bytes.seek(0)
        
        download_name = f'errores_{job.filename}'
        
        return send_file(
            file_bytes,
            mimetype='text/csv',
            as_attachment=True,
            download_name=download_name
        )
        
    except ApiError:
        raise
    except Exception as e:
        raise ApiError(f"Error al generar archivo de errores: {str(e)}", 500)


@bulk_upload_bp.route('/<job_id>/cancel', methods=['POST'])
def cancel_job(job_id):
    """
    POST /api/products/bulk-upload/{job_id}/cancel
    
    Cancela un job que está pendiente o en validación.
    
    Returns:
        {
            "message": "Job cancelado exitosamente",
            "job": {...}
        }
    """
    try:
        job = BulkUploadJob.query.filter_by(job_id=job_id).first()
        
        if not job:
            raise ApiError(f"Job {job_id} no encontrado", 404)
        
        if not job.can_be_cancelled():
            raise ApiError(
                f"Job en estado '{job.status}' no puede ser cancelado. "
                "Solo se pueden cancelar jobs en estado 'pending' o 'validating'.",
                 400
            )
        
        job.set_status(JobStatus.CANCELLED)
        job.set_error_message('Cancelado por el usuario')
        db.session.commit()
        
        return jsonify({
            'message': 'Job cancelado exitosamente',
            'job': job.to_dict()
        }), 200
        
    except ApiError:
        raise
    except Exception as e:
        raise ApiError(f"Error al cancelar job: {str(e)}", 500)


@bulk_upload_bp.route('/stats', methods=['GET'])
def get_upload_stats():
    """
    GET /api/products/bulk-upload/stats
    
    Obtiene estadísticas generales de cargas masivas.
    
    Returns:
        {
            "total_jobs": 125,
            "completed": 100,
            "failed": 5,
            "in_progress": 3,
            "total_products_imported": 15230,
            "average_success_rate": 94.5
        }
    """
    try:
        total_jobs = BulkUploadJob.query.count()
        completed = BulkUploadJob.query.filter_by(status=JobStatus.COMPLETED).count()
        failed = BulkUploadJob.query.filter_by(status=JobStatus.FAILED).count()
        in_progress = BulkUploadJob.query.filter(
            BulkUploadJob.status.in_([JobStatus.PENDING, JobStatus.VALIDATING, JobStatus.PROCESSING])
        ).count()
        
        # Total de productos importados exitosamente
        total_products = db.session.query(
            db.func.sum(BulkUploadJob.successful_rows)
        ).filter_by(status=JobStatus.COMPLETED).scalar() or 0
        
        # Tasa de éxito promedio
        completed_jobs = BulkUploadJob.query.filter_by(status=JobStatus.COMPLETED).all()
        if completed_jobs:
            success_rates = [job.get_success_rate() for job in completed_jobs]
            avg_success_rate = round(sum(success_rates) / len(success_rates), 2)
        else:
            avg_success_rate = 0.0
        
        return jsonify({
            'total_jobs': total_jobs,
            'completed': completed,
            'failed': failed,
            'in_progress': in_progress,
            'cancelled': BulkUploadJob.query.filter_by(status=JobStatus.CANCELLED).count(),
            'total_products_imported': int(total_products),
            'average_success_rate': avg_success_rate
        }), 200
        
    except Exception as e:
        raise ApiError(f"Error al obtener estadísticas: {str(e)}", 500)
