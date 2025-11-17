"""
Tests for get_sales_summary_report command.
"""
import pytest
from datetime import datetime, date
from decimal import Decimal
from src.commands.get_sales_summary_report import GetSalesSummaryReport
from src.models.order import Order
from src.models.order_item import OrderItem
from src.entities.salesperson import Salesperson
from src.entities.salesperson_goal import SalespersonGoal, GoalType, Region, Quarter
from src.errors.errors import ValidationError


class TestGetSalesSummaryReport:
    """Test suite for GetSalesSummaryReport command."""
    
    @pytest.fixture
    def setup_test_data(self, db, sample_customer, app):
        """Setup comprehensive test data for sales reports."""
        with app.app_context():
            # Create salesperson
            salesperson1 = Salesperson(
                employee_id='EMP-TEST-001',
                first_name='Juan',
                last_name='Pérez',
                email='juan.perez@test.com',
                phone='+57 300 1234567',
                territory='Norte',
                hire_date=date(2023, 1, 1),
                is_active=True
            )
            
            db.session.add(salesperson1)
            db.session.flush()
            
            # Create goals - unidades en Norte, monetario en Sur (diferentes regiones)
            goal1_units = SalespersonGoal(
                id_vendedor='EMP-TEST-001',
                id_producto='MED-001',
                region=Region.NORTE.value,
                trimestre=Quarter.Q4.value,
                valor_objetivo=200.0,
                tipo=GoalType.UNIDADES.value
            )
            
            goal1_amount = SalespersonGoal(
                id_vendedor='EMP-TEST-001',
                id_producto='MED-001',
                region=Region.SUR.value,
                trimestre=Quarter.Q4.value,
                valor_objetivo=3000000.0,
                tipo=GoalType.MONETARIO.value
            )
            
            db.session.add(goal1_units)
            db.session.add(goal1_amount)
            
            # Create order
            order1 = Order(
                order_number='ORD-2025-TEST-001',
                customer_id=sample_customer.id,
                seller_id='EMP-TEST-001',
                seller_name='Juan Pérez',
                status='confirmed',
                subtotal=Decimal('500000.00'),
                discount_amount=Decimal('0.00'),
                tax_amount=Decimal('95000.00'),
                total_amount=Decimal('595000.00'),
                payment_terms='credito_30',
                payment_method='transferencia',
                order_date=datetime(2025, 11, 15)
            )
            db.session.add(order1)
            db.session.flush()
            
            # Order item
            item1_1 = OrderItem(
                order_id=order1.id,
                product_sku='MED-001',
                product_name='Ibuprofeno 400mg x 30',
                quantity=10,
                unit_price=Decimal('17850.00'),
                discount_percentage=Decimal('0.0'),
                discount_amount=Decimal('0.00'),
                tax_percentage=Decimal('19.0'),
                tax_amount=Decimal('33915.00'),
                subtotal=Decimal('178500.00'),
                total=Decimal('212415.00'),
                distribution_center_code='DC-001',
                stock_confirmed=True
            )
            
            db.session.add(item1_1)
            db.session.commit()
            
            return {
                'salesperson1': salesperson1,
                'order1': order1
            }
    
    def test_multiple_rows_per_sale(self, setup_test_data, app):
        """Test that one sale generates multiple rows (one per tipo_objetivo)."""
        with app.app_context():
            command = GetSalesSummaryReport(
                employee_id='EMP-TEST-001',
                month=11,
                year=2025
            )
            result = command.execute()
            
            # Should have 2 rows: one for unidades (Norte), one for monetario (Sur)
            assert result['total_records'] == 2
            assert len(result['summary']) == 2
            
            # Verify both tipos are present
            tipos = [item['tipo_objetivo'] for item in result['summary']]
            assert 'unidades' in tipos
            assert 'monetario' in tipos
            
            # Verify both regions are present
            regions = [item['region'] for item in result['summary']]
            assert 'Norte' in regions
            assert 'Sur' in regions
    
    def test_response_structure_v1_0_0(self, setup_test_data, app):
        """Test that response structure matches v1.0.0 specification."""
        with app.app_context():
            command = GetSalesSummaryReport(month=11, year=2025)
            result = command.execute()
            
            assert len(result['summary']) > 0
            item = result['summary'][0]
            
            # Required fields for v1.0.0
            required_fields = [
                'fecha', 'employee_id', 'vendedor', 'region', 'territory',
                'product_sku', 'product_name', 'tipo_objetivo',
                'volumen_ventas', 'valor_total', 'valor_objetivo',
                'cumplimiento_porcentaje'
            ]
            
            for field in required_fields:
                assert field in item, f"Missing field: {field}"
            
            # tipo_objetivo should be either 'unidades' or 'monetario'
            assert item['tipo_objetivo'] in ['unidades', 'monetario']
    
    def test_filter_by_region(self, setup_test_data, app):
        """Test filtering by region shows only that region."""
        with app.app_context():
            # Filter for Norte
            command = GetSalesSummaryReport(region='Norte', month=11, year=2025)
            result = command.execute()
            
            # Should only have Norte records
            for item in result['summary']:
                assert item['region'] == 'Norte'
                assert item['tipo_objetivo'] == 'unidades'  # Norte has unidades in our test data
    
    def test_filter_by_employee_id(self, setup_test_data, app):
        """Test filtering by employee_id."""
        with app.app_context():
            command = GetSalesSummaryReport(employee_id='EMP-TEST-001')
            result = command.execute()
            
            # All records should be for this employee
            for item in result['summary']:
                assert item['employee_id'] == 'EMP-TEST-001'
                assert 'Juan Pérez' in item['vendedor']
    
    def test_cumplimiento_calculation_unidades(self, setup_test_data, app):
        """Test achievement percentage calculation for unidades."""
        with app.app_context():
            command = GetSalesSummaryReport(
                employee_id='EMP-TEST-001',
                region='Norte',  # unidades
                month=11,
                year=2025
            )
            result = command.execute()
            
            item = result['summary'][0]
            
            # Verify calculation: (10 / 200) * 100 = 5.0
            assert item['tipo_objetivo'] == 'unidades'
            assert item['valor_objetivo'] == 200.0
            assert item['volumen_ventas'] == 10
            assert item['cumplimiento_porcentaje'] == 5.0
    
    def test_cumplimiento_calculation_monetario(self, setup_test_data, app):
        """Test achievement percentage calculation for monetario."""
        with app.app_context():
            command = GetSalesSummaryReport(
                employee_id='EMP-TEST-001',
                region='Sur',  # monetario
                month=11,
                year=2025
            )
            result = command.execute()
            
            item = result['summary'][0]
            
            # Verify calculation: (212415 / 3000000) * 100
            assert item['tipo_objetivo'] == 'monetario'
            assert item['valor_objetivo'] == 3000000.0
            assert item['valor_total'] == 212415.0
            expected = round((212415.0 / 3000000.0) * 100, 2)
            assert item['cumplimiento_porcentaje'] == expected
    
    def test_invalid_month_raises_error(self, app):
        """Test that invalid month raises ValidationError."""
        with app.app_context():
            with pytest.raises(ValidationError) as exc_info:
                command = GetSalesSummaryReport(month=13)
                command.execute()
            
            assert 'Month must be between 1 and 12' in str(exc_info.value)
    
    def test_invalid_year_raises_error(self, app):
        """Test that invalid year raises ValidationError."""
        with app.app_context():
            with pytest.raises(ValidationError) as exc_info:
                command = GetSalesSummaryReport(year=1999)
                command.execute()
            
            assert 'Invalid year' in str(exc_info.value)
    
    def test_empty_result_structure(self, app):
        """Test that empty result still has proper structure."""
        with app.app_context():
            command = GetSalesSummaryReport(month=1, year=2020)
            result = command.execute()
            
            assert result['total_records'] == 0
            assert result['summary'] == []
            assert 'totals' in result
            assert 'filters_applied' in result
    
    def test_totals_calculation(self, setup_test_data, app):
        """Test that totals are calculated correctly."""
        with app.app_context():
            command = GetSalesSummaryReport(month=11, year=2025)
            result = command.execute()
            
            totals = result['totals']
            
            assert 'total_volumen_ventas' in totals
            assert 'total_valor_total' in totals
            assert 'unique_salespersons' in totals
            assert 'unique_products' in totals
            assert 'unique_regions' in totals
