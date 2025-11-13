"""
Tests for reports blueprints.
"""
import pytest
from datetime import datetime, timedelta, date
from decimal import Decimal
from src.models.order import Order
from src.models.order_item import OrderItem
from src.models.customer import Customer
from src.entities.salesperson import Salesperson
from src.entities.salesperson_goal import SalespersonGoal, GoalType, Region, Quarter


class TestReportsBlueprint:
    """Test suite for reports blueprint endpoints."""
    
    @pytest.fixture
    def setup_sales_data(self, db, sample_customer):
        """Setup comprehensive sales data for testing."""
        # Create salesperson
        salesperson = Salesperson(
            employee_id='EMP-TEST-001',
            first_name='Carlos',
            last_name='Rodríguez',
            email='carlos@test.com',
            phone='+57 300 1111111',
            territory='Centro',
            hire_date=date(2023, 1, 1),
            is_active=True
        )
        db.session.add(salesperson)
        db.session.flush()
        
        # Create goals - diferentes regiones para unidades y monetario
        goal_units = SalespersonGoal(
            id_vendedor='EMP-TEST-001',
            id_producto='PROD-001',
            region=Region.NORTE.value,
            trimestre=Quarter.Q4.value,
            valor_objetivo=100.0,
            tipo=GoalType.UNIDADES.value
        )
        
        goal_amount = SalespersonGoal(
            id_vendedor='EMP-TEST-001',
            id_producto='PROD-001',
            region=Region.SUR.value,  # Diferente región
            trimestre=Quarter.Q4.value,
            valor_objetivo=1000000.0,
            tipo=GoalType.MONETARIO.value
        )
        
        db.session.add(goal_units)
        db.session.add(goal_amount)
        
        # Create order
        order = Order(
            order_number='ORD-TEST-001',
            customer_id=sample_customer.id,
            seller_id='EMP-TEST-001',
            seller_name='Carlos Rodríguez',
            status='confirmed',
            subtotal=Decimal('100000.00'),
            discount_amount=Decimal('0.00'),
            tax_amount=Decimal('19000.00'),
            total_amount=Decimal('119000.00'),
            payment_terms='credito_30',
            payment_method='transferencia',
            order_date=datetime(2025, 11, 10)
        )
        db.session.add(order)
        db.session.flush()
        
        # Create order item
        item = OrderItem(
            order_id=order.id,
            product_sku='PROD-001',
            product_name='Test Product',
            quantity=50,
            unit_price=Decimal('2000.00'),
            discount_percentage=Decimal('0.0'),
            discount_amount=Decimal('0.00'),
            tax_percentage=Decimal('19.0'),
            tax_amount=Decimal('19000.00'),
            subtotal=Decimal('100000.00'),
            total=Decimal('119000.00'),
            distribution_center_code='DC-001',
            stock_confirmed=True
        )
        db.session.add(item)
        db.session.commit()
        
        return {
            'salesperson': salesperson,
            'order': order,
            'item': item
        }
    
    def test_sales_summary_invalid_month(self, client):
        """Test validation error with invalid month."""
        response = client.get('/reports/sales-summary?month=invalid')
        
        assert response.status_code == 400
        data = response.get_json()
        
        assert 'error' in data
        assert 'Month must be a valid integer' in data['error']
    
    def test_sales_summary_invalid_year(self, client):
        """Test validation error with invalid year."""
        response = client.get('/reports/sales-summary?year=invalid')
        
        assert response.status_code == 400
        data = response.get_json()
        
        assert 'error' in data
        assert 'Year must be a valid integer' in data['error']
    
    def test_sales_summary_month_out_of_range(self, client):
        """Test validation error with month out of range."""
        response = client.get('/reports/sales-summary?month=13')
        
        assert response.status_code == 400
        data = response.get_json()
        
        assert 'error' in data
    
    def test_sales_summary_invalid_date_format(self, client):
        """Test validation error with invalid date format."""
        response = client.get('/reports/sales-summary?from_date=invalid-date')
        
        assert response.status_code == 400
        data = response.get_json()
        
        assert 'error' in data
    
    def test_reports_health_check(self, client):
        """Test reports health check endpoint."""
        response = client.get('/reports/health')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['service'] == 'reports'
        assert data['status'] == 'healthy'
        assert 'endpoints' in data
        assert len(data['endpoints']) >= 3
    
    def test_sales_summary_empty_result(self, client):
        """Test getting sales summary with no data."""
        response = client.get('/reports/sales-summary')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert 'summary' in data
        assert 'totals' in data
        assert 'filters_applied' in data
        assert 'total_records' in data
        assert isinstance(data['summary'], list)
        assert data['total_records'] == 0
        assert data['summary'] == []
    
    def test_sales_summary_with_data(self, client, setup_sales_data):
        """Test getting sales summary with actual data (v1.0.0 - multiple rows)."""
        response = client.get('/reports/sales-summary?month=11&year=2025')
        
        assert response.status_code == 200
        data = response.get_json()
        
        # v1.0.0: Should have 2 rows (one per tipo/region)
        assert data['total_records'] == 2
        assert len(data['summary']) == 2
        
        # Verify both tipos exist
        tipos = [item['tipo_objetivo'] for item in data['summary']]
        assert 'unidades' in tipos
        assert 'monetario' in tipos
        
        # Check structure of first item
        item = data['summary'][0]
        
        # Verify structure v1.0.0
        assert 'fecha' in item
        assert 'employee_id' in item
        assert 'vendedor' in item
        assert 'region' in item
        assert 'product_sku' in item
        assert 'product_name' in item
        assert 'tipo_objetivo' in item
        assert 'volumen_ventas' in item
        assert 'valor_total' in item
        assert 'valor_objetivo' in item
        assert 'cumplimiento_porcentaje' in item
        
        # Verify common values
        for item in data['summary']:
            assert item['employee_id'] == 'EMP-TEST-001'
            assert item['product_sku'] == 'PROD-001'
            assert item['volumen_ventas'] == 50
    
    def test_sales_summary_filter_by_employee(self, client, setup_sales_data):
        """Test filtering sales summary by employee_id."""
        response = client.get('/reports/sales-summary?employee_id=EMP-TEST-001')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['total_records'] >= 1
        assert data['filters_applied']['employee_id'] == 'EMP-TEST-001'
        
        # All records should be for this employee
        for item in data['summary']:
            assert item['employee_id'] == 'EMP-TEST-001'
    
    def test_sales_summary_filter_by_product(self, client, setup_sales_data):
        """Test filtering sales summary by product_sku."""
        response = client.get('/reports/sales-summary?product_sku=PROD-001')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['total_records'] >= 1
        assert data['filters_applied']['product_sku'] == 'PROD-001'
        
        # All records should be for this product
        for item in data['summary']:
            assert item['product_sku'] == 'PROD-001'
    
    def test_sales_summary_filter_by_territory(self, client, setup_sales_data):
        """Test filtering sales summary by territory."""
        response = client.get('/reports/sales-summary?territory=Centro')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['filters_applied']['territory'] == 'Centro'
        
        # All records should be for this territory
        for item in data['summary']:
            assert item['territory'] == 'Centro'
    
    def test_sales_summary_combined_filters(self, client, setup_sales_data):
        """Test combining multiple filters."""
        response = client.get(
            '/reports/sales-summary?employee_id=EMP-TEST-001&month=11&year=2025'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['filters_applied']['employee_id'] == 'EMP-TEST-001'
        assert data['filters_applied']['month'] == 11
        assert data['filters_applied']['year'] == 2025
    
    def test_sales_summary_structure_v1_0_0(self, client, setup_sales_data):
        """Test that response has v1.0.0 structure (single objetivo per row)."""
        response = client.get('/reports/sales-summary?month=11&year=2025')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert len(data['summary']) > 0
        item = data['summary'][0]
        
        # v1.0.0 fields should exist
        assert 'tipo_objetivo' in item
        assert 'valor_objetivo' in item
        assert 'cumplimiento_porcentaje' in item
        
        # tipo_objetivo should be either 'unidades' or 'monetario'
        assert item['tipo_objetivo'] in ['unidades', 'monetario']
        
        # Old v1.0.2 dual structure fields should NOT exist
        assert 'objetivo_unidades' not in item
        assert 'objetivo_monetario' not in item
        assert 'cumplimiento_unidades' not in item
        assert 'cumplimiento_monetario' not in item
    
    def test_sales_summary_multiple_rows_per_sale(self, client, db, sample_customer):
        """Test that same (date, vendor, product) creates multiple rows (v1.0.0 behavior)."""
        # Create salesperson
        salesperson = Salesperson(
            employee_id='EMP-MULTI-TEST',
            first_name='Test',
            last_name='Multiple',
            email='test@multi.com',
            phone='+57 300 9999999',
            territory='Test',
            hire_date=date(2023, 1, 1),
            is_active=True
        )
        db.session.add(salesperson)
        db.session.flush()
        
        # Create TWO goals with DIFFERENT regions
        goal1 = SalespersonGoal(
            id_vendedor='EMP-MULTI-TEST',
            id_producto='MULTI-001',
            region=Region.NORTE.value,
            trimestre=Quarter.Q4.value,
            valor_objetivo=100.0,
            tipo=GoalType.UNIDADES.value
        )
        
        goal2 = SalespersonGoal(
            id_vendedor='EMP-MULTI-TEST',
            id_producto='MULTI-001',
            region=Region.SUR.value,
            trimestre=Quarter.Q4.value,
            valor_objetivo=1000000.0,
            tipo=GoalType.MONETARIO.value
        )
        
        db.session.add(goal1)
        db.session.add(goal2)
        
        # Create ONE order on ONE date
        order = Order(
            order_number='ORD-MULTI-001',
            customer_id=sample_customer.id,
            seller_id='EMP-MULTI-TEST',
            seller_name='Test Multiple',
            status='confirmed',
            subtotal=Decimal('100000.00'),
            discount_amount=Decimal('0.00'),
            tax_amount=Decimal('19000.00'),
            total_amount=Decimal('119000.00'),
            payment_terms='credito_30',
            payment_method='transferencia',
            order_date=datetime(2025, 11, 15)
        )
        db.session.add(order)
        db.session.flush()
        
        item = OrderItem(
            order_id=order.id,
            product_sku='MULTI-001',
            product_name='Multiple Test Product',
            quantity=10,
            unit_price=Decimal('10000.00'),
            discount_percentage=Decimal('0.0'),
            discount_amount=Decimal('0.00'),
            tax_percentage=Decimal('19.0'),
            tax_amount=Decimal('19000.00'),
            subtotal=Decimal('100000.00'),
            total=Decimal('119000.00'),
            distribution_center_code='DC-001',
            stock_confirmed=True
        )
        db.session.add(item)
        db.session.commit()
        
        # Query the report
        response = client.get('/reports/sales-summary?employee_id=EMP-MULTI-TEST&month=11&year=2025')
        
        assert response.status_code == 200
        data = response.get_json()
        
        # v1.0.0: Should return 2 rows (one per tipo/region combination)
        assert data['total_records'] == 2, "Should have 2 rows in v1.0.0 (one per tipo)"
        
        # Verify both tipos exist
        tipos = [item['tipo_objetivo'] for item in data['summary']]
        assert 'unidades' in tipos
        assert 'monetario' in tipos
        
        # Verify both regions exist
        regions = [item['region'] for item in data['summary']]
        assert 'Norte' in regions
        assert 'Sur' in regions
        
        # Find unidades row
        unidades_row = next(item for item in data['summary'] if item['tipo_objetivo'] == 'unidades')
        assert unidades_row['region'] == 'Norte'
        assert unidades_row['valor_objetivo'] == 100.0
        
        # Find monetario row
        monetario_row = next(item for item in data['summary'] if item['tipo_objetivo'] == 'monetario')
        assert monetario_row['region'] == 'Sur'
        assert monetario_row['valor_objetivo'] == 1000000.0
    
    def test_sales_summary_totals_calculated(self, client, setup_sales_data):
        """Test that totals are properly calculated."""
        response = client.get('/reports/sales-summary?month=11&year=2025')
        
        assert response.status_code == 200
        data = response.get_json()
        
        totals = data['totals']
        
        assert 'total_volumen_ventas' in totals
        assert 'total_valor_total' in totals
        
        # Verify totals match sum of summary
        expected_volume = sum(item['volumen_ventas'] for item in data['summary'])
        expected_value = sum(item['valor_total'] for item in data['summary'])
        
        assert totals['total_volumen_ventas'] == expected_volume
        assert totals['total_valor_total'] == expected_value
    
    def test_sales_by_salesperson_empty_result(self, client):
        """Test getting sales by salesperson with no data."""
        response = client.get('/reports/sales-by-salesperson')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert 'salespersons' in data
        assert 'total_salespersons' in data
        assert 'filters_applied' in data
    
    def test_sales_by_product_empty_result(self, client):
        """Test getting sales by product with no data."""
        response = client.get('/reports/sales-by-product')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert 'products' in data
        assert 'total_products' in data
        assert 'filters_applied' in data
