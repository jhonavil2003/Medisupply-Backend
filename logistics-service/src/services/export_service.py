"""
Servicio de exportación de rutas a PDF y CSV.

Este módulo proporciona funcionalidades para exportar rutas de entrega
en diferentes formatos para conductores y personal logístico.
"""

import os
import io
import csv
import logging
from datetime import datetime

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
)
from reportlab.lib import colors

from src.models.delivery_route import DeliveryRoute
from src.models.route_stop import RouteStop
from src.models.route_assignment import RouteAssignment
from src.models.vehicle import Vehicle
from src.session import Session

logger = logging.getLogger(__name__)


class ExportService:
    """
    Servicio para exportar rutas en diferentes formatos.
    
    Formatos soportados:
    - PDF: Hoja de ruta detallada para conductores
    - CSV: Datos tabulares para análisis
    - JSON: Datos estructurados (ya implementado en to_dict())
    """
    
    # URL para Google Static Maps API
    GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY', '')
    STATIC_MAPS_BASE_URL = 'https://maps.googleapis.com/maps/api/staticmap'
    
    @staticmethod
    def export_route_to_pdf(route_id: int) -> bytes:
        """
        Exporta una ruta a PDF con formato profesional.
        
        El PDF incluye:
        - Encabezado con información del vehículo y conductor
        - Lista secuencial de paradas con detalles
        - Mapa estático de la ruta (si API key disponible)
        - Instrucciones especiales
        - Footer con fecha de generación
        
        Args:
            route_id: ID de la ruta a exportar
        
        Returns:
            bytes: Contenido del PDF
        
        Raises:
            ValueError: Si la ruta no existe
        """
        # Obtener ruta con todas las relaciones
        route = Session.query(DeliveryRoute).filter_by(id=route_id).first()
        
        if not route:
            raise ValueError(f"Ruta {route_id} no encontrada")
        
        # Obtener vehículo
        vehicle = Session.query(Vehicle).filter_by(id=route.vehicle_id).first()
        
        # Obtener paradas ordenadas
        stops = Session.query(RouteStop).filter_by(
            route_id=route_id
        ).order_by(RouteStop.sequence_order).all()
        
        # Crear buffer para PDF
        buffer = io.BytesIO()
        
        # Crear documento PDF
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch
        )
        
        # Estilos
        styles = getSampleStyleSheet()
        
        # Estilo personalizado para título
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1a237e'),
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        # Estilo para subtítulos
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#283593'),
            spaceAfter=10,
            fontName='Helvetica-Bold'
        )
        
        # Estilo para texto normal
        normal_style = styles['Normal']
        
        # Construir elementos del PDF
        elements = []
        
        # ========== ENCABEZADO ==========
        elements.append(Paragraph("🚚 HOJA DE RUTA DE ENTREGA", title_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Información general en tabla
        general_info = [
            ['Código de Ruta:', route.route_code or f"ROUTE-{route.id}"],
            ['Fecha Planeada:', route.planned_date.strftime('%d/%m/%Y') if route.planned_date else 'N/A'],
            ['Estado:', route.status.upper()],
            ['Generado:', datetime.now().strftime('%d/%m/%Y %H:%M')]
        ]
        
        general_table = Table(general_info, colWidths=[2*inch, 4*inch])
        general_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e3f2fd')),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#1565c0')),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elements.append(general_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # ========== INFORMACIÓN DEL VEHÍCULO ==========
        if vehicle:
            elements.append(Paragraph("🚐 INFORMACIÓN DEL VEHÍCULO", subtitle_style))
            elements.append(Spacer(1, 0.1*inch))
            
            vehicle_info = [
                ['Placa:', vehicle.plate or 'N/A'],
                ['Tipo:', vehicle.vehicle_type or 'N/A'],
                ['Conductor:', vehicle.driver_name or 'N/A'],
                ['Teléfono:', vehicle.driver_phone or 'N/A'],
                ['Capacidad:', f"{vehicle.capacity_kg} kg / {vehicle.capacity_m3} m³" if vehicle.capacity_kg else 'N/A'],
                ['Refrigeración:', '✅ Sí' if vehicle.has_refrigeration else '❌ No']
            ]
            
            vehicle_table = Table(vehicle_info, colWidths=[2*inch, 4*inch])
            vehicle_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#fff3e0')),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#e65100')),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            
            elements.append(vehicle_table)
            elements.append(Spacer(1, 0.3*inch))
        
        # ========== RESUMEN DE LA RUTA ==========
        elements.append(Paragraph("📊 RESUMEN DE LA RUTA", subtitle_style))
        elements.append(Spacer(1, 0.1*inch))
        
        summary_info = [
            ['Total de Paradas:', str(route.total_stops or len(stops))],
            ['Total de Pedidos:', str(route.total_orders or 0)],
            ['Distancia Total:', f"{route.total_distance_km or 0:.2f} km" if route.total_distance_km else 'N/A'],
            ['Duración Estimada:', f"{route.estimated_duration_minutes or 0} minutos" if route.estimated_duration_minutes else 'N/A'],
            ['Cadena de Frío:', '✅ Sí' if route.has_cold_chain_products else '❌ No'],
            ['Score de Optimización:', f"{route.optimization_score or 0:.1f}/100" if route.optimization_score else 'N/A']
        ]
        
        summary_table = Table(summary_info, colWidths=[2*inch, 4*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8f5e9')),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#2e7d32')),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elements.append(summary_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # ========== LISTA DE PARADAS ==========
        elements.append(Paragraph("📍 PARADAS DE ENTREGA", subtitle_style))
        elements.append(Spacer(1, 0.1*inch))
        
        if stops:
            for stop in stops:
                # Obtener asignaciones de esta parada
                assignments = Session.query(RouteAssignment).filter_by(
                    stop_id=stop.id
                ).all()
                
                # Encabezado de parada
                stop_header = f"<b>Parada #{stop.sequence_order}</b> - {stop.customer_name or 'Cliente'}"
                if stop.clinical_priority:
                    priority_text = {1: '🔴 CRÍTICO', 2: '🟡 ALTO', 3: '🟢 NORMAL'}.get(stop.clinical_priority, '')
                    stop_header += f" ({priority_text})"
                
                elements.append(Paragraph(stop_header, styles['Heading3']))
                elements.append(Spacer(1, 0.05*inch))
                
                # Detalles de parada
                stop_details = [
                    ['📍 Dirección:', stop.delivery_address or 'N/A'],
                    ['🏙️ Ciudad:', stop.city or 'N/A'],
                    ['🕐 Ventana de Entrega:', 
                     f"{stop.time_window_start.strftime('%H:%M') if stop.time_window_start else 'N/A'} - "
                     f"{stop.time_window_end.strftime('%H:%M') if stop.time_window_end else 'N/A'}"],
                    ['⏰ Llegada Estimada:', 
                     stop.estimated_arrival_time.strftime('%H:%M') if stop.estimated_arrival_time else 'N/A'],
                    ['📦 Pedidos:', ', '.join([a.order_number for a in assignments]) if assignments else 'N/A'],
                    ['⚖️ Peso Total:', 
                     f"{sum([a.total_weight_kg or 0 for a in assignments]):.2f} kg" if assignments else 'N/A'],
                ]
                
                # Agregar instrucciones especiales si existen
                if stop.notes:
                    stop_details.append(['📝 Instrucciones:', stop.notes])
                
                stop_table = Table(stop_details, colWidths=[1.8*inch, 5*inch])
                stop_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f5f5f5')),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 6),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ]))
                
                elements.append(stop_table)
                elements.append(Spacer(1, 0.15*inch))
        else:
            elements.append(Paragraph("No hay paradas registradas para esta ruta.", normal_style))
        
        # ========== NOTAS ADICIONALES ==========
        if route.notes:
            elements.append(Spacer(1, 0.2*inch))
            elements.append(Paragraph("📝 NOTAS ADICIONALES", subtitle_style))
            elements.append(Spacer(1, 0.1*inch))
            elements.append(Paragraph(route.notes, normal_style))
        
        # ========== FOOTER ==========
        elements.append(Spacer(1, 0.3*inch))
        footer_text = f"<i>Documento generado automáticamente por MediSupply - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</i>"
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=TA_CENTER
        )
        elements.append(Paragraph(footer_text, footer_style))
        
        # Construir PDF
        doc.build(elements)
        
        # Obtener contenido del buffer
        pdf_content = buffer.getvalue()
        buffer.close()
        
        logger.info(f"PDF generado para ruta {route_id}: {len(pdf_content)} bytes")
        
        return pdf_content
    
    @staticmethod
    def export_route_to_csv(route_id: int) -> str:
        """
        Exporta una ruta a CSV con datos tabulares.
        
        Columnas:
        - Secuencia
        - Tipo de Parada
        - Cliente
        - Dirección
        - Ciudad
        - Coordenadas
        - Ventana de Entrega (Inicio)
        - Ventana de Entrega (Fin)
        - Hora Estimada de Llegada
        - Pedidos
        - Peso Total (kg)
        - Volumen Total (m³)
        - Prioridad Clínica
        - Instrucciones
        
        Args:
            route_id: ID de la ruta a exportar
        
        Returns:
            str: Contenido CSV
        
        Raises:
            ValueError: Si la ruta no existe
        """
        # Obtener ruta
        route = Session.query(DeliveryRoute).filter_by(id=route_id).first()
        
        if not route:
            raise ValueError(f"Ruta {route_id} no encontrada")
        
        # Obtener paradas ordenadas
        stops = Session.query(RouteStop).filter_by(
            route_id=route_id
        ).order_by(RouteStop.sequence_order).all()
        
        # Crear CSV en memoria
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Encabezado del CSV
        writer.writerow([
            'Secuencia',
            'Tipo',
            'Cliente',
            'Dirección',
            'Ciudad',
            'Latitud',
            'Longitud',
            'Ventana Inicio',
            'Ventana Fin',
            'Llegada Estimada',
            'Pedidos',
            'Peso Total (kg)',
            'Volumen Total (m³)',
            'Prioridad',
            'Instrucciones'
        ])
        
        # Datos de las paradas
        for stop in stops:
            # Obtener asignaciones
            assignments = Session.query(RouteAssignment).filter_by(
                stop_id=stop.id
            ).all()
            
            # Calcular totales
            total_weight = sum([a.total_weight_kg or 0 for a in assignments])
            total_volume = sum([a.total_volume_m3 or 0 for a in assignments])
            order_numbers = ', '.join([a.order_number for a in assignments])
            
            # Prioridad
            priority_map = {1: 'Crítico', 2: 'Alto', 3: 'Normal'}
            priority = priority_map.get(stop.clinical_priority, 'N/A')
            
            writer.writerow([
                stop.sequence_order,
                stop.stop_type or 'delivery',
                stop.customer_name or '',
                stop.delivery_address or '',
                stop.city or '',
                f"{stop.latitude:.7f}" if stop.latitude else '',
                f"{stop.longitude:.7f}" if stop.longitude else '',
                stop.time_window_start.strftime('%H:%M') if stop.time_window_start else '',
                stop.time_window_end.strftime('%H:%M') if stop.time_window_end else '',
                stop.estimated_arrival_time.strftime('%H:%M') if stop.estimated_arrival_time else '',
                order_numbers,
                f"{total_weight:.2f}",
                f"{total_volume:.3f}",
                priority,
                stop.notes or ''
            ])
        
        csv_content = output.getvalue()
        output.close()
        
        logger.info(f"CSV generado para ruta {route_id}: {len(csv_content)} caracteres")
        
        return csv_content
    
    @staticmethod
    def export_daily_routes_summary(
        distribution_center_id: int,
        planned_date
    ) -> bytes:
        """
        Genera un resumen ejecutivo en PDF de todas las rutas del día.
        
        Incluye:
        - Resumen general (total rutas, pedidos, distancia)
        - Tabla con todas las rutas
        - Estadísticas por vehículo
        - Gráfico de distribución (si es posible)
        
        Args:
            distribution_center_id: ID del centro de distribución
            planned_date: Fecha de las rutas
        
        Returns:
            bytes: Contenido del PDF
        """
        # Obtener todas las rutas del día
        routes = Session.query(DeliveryRoute).filter_by(
            distribution_center_id=distribution_center_id,
            planned_date=planned_date
        ).all()
        
        if not routes:
            raise ValueError(f"No hay rutas para DC {distribution_center_id} en {planned_date}")
        
        # Crear buffer para PDF
        buffer = io.BytesIO()
        
        # Crear documento PDF
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch
        )
        
        # Estilos
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#1a237e'),
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        elements = []
        
        # Título
        elements.append(Paragraph(
            f"📊 RESUMEN DIARIO DE RUTAS - {planned_date.strftime('%d/%m/%Y')}",
            title_style
        ))
        elements.append(Spacer(1, 0.3*inch))
        
        # Calcular métricas
        total_routes = len(routes)
        total_orders = sum([r.total_orders or 0 for r in routes])
        total_distance = sum([r.total_distance_km or 0 for r in routes])
        total_stops = sum([r.total_stops or 0 for r in routes])
        
        # Tabla de resumen
        summary = [
            ['Métrica', 'Valor'],
            ['Total de Rutas', str(total_routes)],
            ['Total de Pedidos', str(total_orders)],
            ['Total de Paradas', str(total_stops)],
            ['Distancia Total', f"{total_distance:.2f} km"],
            ['Distancia Promedio', f"{total_distance/total_routes:.2f} km" if total_routes > 0 else 'N/A']
        ]
        
        summary_table = Table(summary, colWidths=[3*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1565c0')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ]))
        
        elements.append(summary_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Tabla detallada de rutas
        elements.append(Paragraph("📋 DETALLE DE RUTAS", styles['Heading2']))
        elements.append(Spacer(1, 0.1*inch))
        
        route_data = [['Código', 'Vehículo', 'Paradas', 'Pedidos', 'Distancia', 'Estado']]
        
        for route in routes:
            vehicle = Session.query(Vehicle).filter_by(id=route.vehicle_id).first()
            route_data.append([
                route.route_code or f"R-{route.id}",
                vehicle.plate if vehicle else 'N/A',
                str(route.total_stops or 0),
                str(route.total_orders or 0),
                f"{route.total_distance_km or 0:.1f} km",
                route.status.upper()
            ])
        
        route_table = Table(route_data, colWidths=[1.5*inch, 1*inch, 0.8*inch, 0.8*inch, 1*inch, 1*inch])
        route_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ]))
        
        elements.append(route_table)
        
        # Construir PDF
        doc.build(elements)
        
        pdf_content = buffer.getvalue()
        buffer.close()
        
        logger.info(f"Resumen diario generado: {len(pdf_content)} bytes")
        
        return pdf_content


# Instancia singleton
_export_service_instance = None


def get_export_service() -> ExportService:
    """Retorna instancia singleton del servicio de exportación."""
    global _export_service_instance
    
    if _export_service_instance is None:
        _export_service_instance = ExportService()
    
    return _export_service_instance
