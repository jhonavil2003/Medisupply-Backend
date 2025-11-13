"""
Blueprint for sales reports endpoints.
Provides aggregated reports and analytics for sales data.
"""
from flask import Blueprint, request, jsonify
from src.commands.get_sales_summary_report import GetSalesSummaryReport
from src.errors.errors import ApiError, ValidationError

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')


@reports_bp.route('/sales-summary', methods=['GET'])
def get_sales_summary():
    """
    Get aggregated sales summary report.
    
    Combines order data, items, salespersons, and goals to provide
    comprehensive sales analysis.
    
    Query Parameters:
        - from_date (str): Start date filter (YYYY-MM-DD)
        - to_date (str): End date filter (YYYY-MM-DD)
        - month (int): Month filter (1-12)
        - year (int): Year filter (e.g., 2024)
        - region (str): Filter by salesperson region
        - territory (str): Filter by salesperson territory
        - product_sku (str): Filter by product SKU
        - employee_id (str): Filter by salesperson employee ID
        - order_status (str): Filter by order status
    
    Returns:
        200: JSON with summary data, totals, and metadata
        400: Validation error
        500: Server error
    
    Example:
        GET /reports/sales-summary?region=Andina&month=10&year=2024
        
    Response:
        {
            "summary": [
                {
                    "fecha": "2024-10-15",
                    "employee_id": "EMP-001",
                    "vendedor": "Juan Pérez",
                    "region": "Andina",
                    "territory": "Bogotá",
                    "product_sku": "MED-001",
                    "product_name": "Producto A",
                    "volumen_ventas": 100,
                    "valor_total": 150000.00,
                    "target_quantity": 120,
                    "target_amount": 180000.00,
                    "achievement_quantity_percent": 83.33,
                    "achievement_amount_percent": 83.33
                }
            ],
            "totals": {
                "total_volumen_ventas": 500,
                "total_valor_total": 750000.00,
                "unique_salespersons": 5,
                "unique_products": 10,
                "unique_regions": 3
            },
            "filters_applied": {
                "region": "Andina",
                "month": 10,
                "year": 2024
            },
            "total_records": 25
        }
    """
    try:
        # Get query parameters
        from_date = request.args.get('from_date')
        to_date = request.args.get('to_date')
        region = request.args.get('region')
        territory = request.args.get('territory')
        product_sku = request.args.get('product_sku')
        employee_id = request.args.get('employee_id')
        order_status = request.args.get('order_status')
        
        # Get month and year (convert to int if provided)
        month = request.args.get('month')
        year = request.args.get('year')
        
        if month:
            try:
                month = int(month)
            except ValueError:
                raise ValidationError('Month must be a valid integer (1-12)')
        
        if year:
            try:
                year = int(year)
            except ValueError:
                raise ValidationError('Year must be a valid integer')
        
        # Execute command
        command = GetSalesSummaryReport(
            from_date=from_date,
            to_date=to_date,
            region=region,
            territory=territory,
            product_sku=product_sku,
            employee_id=employee_id,
            month=month,
            year=year,
            order_status=order_status
        )
        
        result = command.execute()
        
        return jsonify(result), 200
        
    except ValidationError as e:
        return jsonify({
            'error': str(e),
            'error_type': 'validation_error'
        }), 400
        
    except ApiError as e:
        return jsonify({
            'error': str(e),
            'error_type': 'api_error'
        }), e.status_code
        
    except Exception as e:
        return jsonify({
            'error': f'Unexpected error generating sales summary: {str(e)}',
            'error_type': 'server_error'
        }), 500


@reports_bp.route('/sales-by-salesperson', methods=['GET'])
def get_sales_by_salesperson():
    """
    Get sales summary grouped by salesperson.
    
    Similar to sales-summary but with additional aggregation by salesperson.
    
    Query Parameters:
        Same as /sales-summary
    
    Returns:
        200: JSON with salesperson-level aggregated data
    """
    try:
        # Get query parameters
        from_date = request.args.get('from_date')
        to_date = request.args.get('to_date')
        region = request.args.get('region')
        territory = request.args.get('territory')
        month = request.args.get('month')
        year = request.args.get('year')
        
        if month:
            month = int(month)
        if year:
            year = int(year)
        
        # Execute command
        command = GetSalesSummaryReport(
            from_date=from_date,
            to_date=to_date,
            region=region,
            territory=territory,
            month=month,
            year=year
        )
        
        result = command.execute()
        
        # Group by salesperson
        salesperson_summary = {}
        for item in result['summary']:
            emp_id = item['employee_id']
            if emp_id not in salesperson_summary:
                salesperson_summary[emp_id] = {
                    'employee_id': emp_id,
                    'vendedor': item['vendedor'],
                    'region': item['region'],
                    'territory': item['territory'],
                    'total_ventas': 0,
                    'total_valor': 0.0,
                    'productos_vendidos': []
                }
            
            salesperson_summary[emp_id]['total_ventas'] += item['volumen_ventas']
            salesperson_summary[emp_id]['total_valor'] += item['valor_total']
            salesperson_summary[emp_id]['productos_vendidos'].append({
                'product_sku': item['product_sku'],
                'product_name': item['product_name'],
                'cantidad': item['volumen_ventas'],
                'valor': item['valor_total']
            })
        
        return jsonify({
            'salespersons': list(salesperson_summary.values()),
            'total_salespersons': len(salesperson_summary),
            'filters_applied': result['filters_applied']
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': f'Error generating salesperson summary: {str(e)}'
        }), 500


@reports_bp.route('/sales-by-product', methods=['GET'])
def get_sales_by_product():
    """
    Get sales summary grouped by product.
    
    Query Parameters:
        Same as /sales-summary
    
    Returns:
        200: JSON with product-level aggregated data
    """
    try:
        # Get query parameters
        from_date = request.args.get('from_date')
        to_date = request.args.get('to_date')
        region = request.args.get('region')
        product_sku = request.args.get('product_sku')
        month = request.args.get('month')
        year = request.args.get('year')
        
        if month:
            month = int(month)
        if year:
            year = int(year)
        
        # Execute command
        command = GetSalesSummaryReport(
            from_date=from_date,
            to_date=to_date,
            region=region,
            product_sku=product_sku,
            month=month,
            year=year
        )
        
        result = command.execute()
        
        # Group by product
        product_summary = {}
        for item in result['summary']:
            sku = item['product_sku']
            if sku not in product_summary:
                product_summary[sku] = {
                    'product_sku': sku,
                    'product_name': item['product_name'],
                    'total_cantidad': 0,
                    'total_valor': 0.0,
                    'vendedores': []
                }
            
            product_summary[sku]['total_cantidad'] += item['volumen_ventas']
            product_summary[sku]['total_valor'] += item['valor_total']
            
            # Add unique salespersons
            if item['employee_id'] not in [v['employee_id'] for v in product_summary[sku]['vendedores']]:
                product_summary[sku]['vendedores'].append({
                    'employee_id': item['employee_id'],
                    'vendedor': item['vendedor']
                })
        
        return jsonify({
            'products': list(product_summary.values()),
            'total_products': len(product_summary),
            'filters_applied': result['filters_applied']
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': f'Error generating product summary: {str(e)}'
        }), 500


@reports_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for reports service."""
    return jsonify({
        'service': 'reports',
        'status': 'healthy',
        'endpoints': [
            '/reports/sales-summary',
            '/reports/sales-by-salesperson',
            '/reports/sales-by-product'
        ]
    }), 200
