import json
from unittest.mock import patch, MagicMock
from src.entities.salesperson_goal import GoalType, Region, Quarter


class TestSalespersonGoalsBlueprint:
    """Test cases for salesperson goals blueprint endpoints"""
    
    # ==================== CREATE (POST) ====================
    
    @patch('src.commands.create_salesperson_goal.IntegrationService')
    def test_create_goal_success(self, mock_integration, client, sample_salesperson):
        """Test POST /salesperson-goals/ - create new goal successfully."""
        # Mock IntegrationService
        mock_service = MagicMock()
        mock_service.get_product_by_sku.return_value = {
            'sku': 'JER-001',
            'name': 'Jeringa 3ml',
            'is_active': True,
            'unit_price': 0.35
        }
        mock_integration.return_value = mock_service
        
        goal_data = {
            'id_vendedor': sample_salesperson.employee_id,
            'id_producto': 'JER-001',
            'region': Region.NORTE.value,
            'trimestre': Quarter.Q1.value,
            'valor_objetivo': 50000.00,
            'tipo': GoalType.MONETARIO.value
        }
        
        response = client.post('/salesperson-goals/',
                              data=json.dumps(goal_data),
                              content_type='application/json')
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'goal' in data
        assert 'message' in data
        assert data['goal']['id_vendedor'] == sample_salesperson.employee_id
        assert data['goal']['id_producto'] == 'JER-001'
        assert data['goal']['region'] == Region.NORTE.value
        assert data['goal']['trimestre'] == Quarter.Q1.value
        assert data['goal']['valor_objetivo'] == 50000.00
        assert data['goal']['tipo'] == GoalType.MONETARIO.value
    
    def test_create_goal_missing_data(self, client):
        """Test POST /salesperson-goals/ - missing required data."""
        response = client.post('/salesperson-goals/',
                              data=json.dumps({}),
                              content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_create_goal_no_json(self, client):
        """Test POST /salesperson-goals/ - no JSON provided."""
        response = client.post('/salesperson-goals/')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'No se proporcionó ningún dato' in data['error']
    
    def test_create_goal_invalid_region(self, client, sample_salesperson):
        """Test POST /salesperson-goals/ - invalid region."""
        goal_data = {
            'id_vendedor': sample_salesperson.employee_id,
            'id_producto': 'JER-001',
            'region': 'InvalidRegion',
            'trimestre': Quarter.Q1.value,
            'valor_objetivo': 50000.00,
            'tipo': GoalType.MONETARIO.value
        }
        
        response = client.post('/salesperson-goals/',
                              data=json.dumps(goal_data),
                              content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_create_goal_invalid_quarter(self, client, sample_salesperson):
        """Test POST /salesperson-goals/ - invalid quarter."""
        goal_data = {
            'id_vendedor': sample_salesperson.employee_id,
            'id_producto': 'JER-001',
            'region': Region.NORTE.value,
            'trimestre': 'Q5',
            'valor_objetivo': 50000.00,
            'tipo': GoalType.MONETARIO.value
        }
        
        response = client.post('/salesperson-goals/',
                              data=json.dumps(goal_data),
                              content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_create_goal_invalid_tipo(self, client, sample_salesperson):
        """Test POST /salesperson-goals/ - invalid goal type."""
        goal_data = {
            'id_vendedor': sample_salesperson.employee_id,
            'id_producto': 'JER-001',
            'region': Region.NORTE.value,
            'trimestre': Quarter.Q1.value,
            'valor_objetivo': 50000.00,
            'tipo': 'invalid_type'
        }
        
        response = client.post('/salesperson-goals/',
                              data=json.dumps(goal_data),
                              content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_create_goal_nonexistent_salesperson(self, client):
        """Test POST /salesperson-goals/ - salesperson doesn't exist."""
        goal_data = {
            'id_vendedor': 'NONEXISTENT-SELLER',
            'id_producto': 'JER-001',
            'region': Region.NORTE.value,
            'trimestre': Quarter.Q1.value,
            'valor_objetivo': 50000.00,
            'tipo': GoalType.MONETARIO.value
        }
        
        response = client.post('/salesperson-goals/',
                              data=json.dumps(goal_data),
                              content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    @patch('src.commands.create_salesperson_goal.IntegrationService')
    def test_create_goal_duplicate(self, mock_integration, client, sample_salesperson_goal):
        """Test POST /salesperson-goals/ - duplicate goal."""
        # Mock IntegrationService
        mock_service = MagicMock()
        mock_service.get_product_by_sku.return_value = {
            'sku': 'JER-001',
            'name': 'Jeringa 3ml',
            'is_active': True,
            'unit_price': 0.35
        }
        mock_integration.return_value = mock_service
        
        # Try to create duplicate goal
        goal_data = {
            'id_vendedor': sample_salesperson_goal.id_vendedor,
            'id_producto': sample_salesperson_goal.id_producto,
            'region': sample_salesperson_goal.region,
            'trimestre': sample_salesperson_goal.trimestre,
            'valor_objetivo': 60000.00,
            'tipo': GoalType.MONETARIO.value
        }
        
        response = client.post('/salesperson-goals/',
                              data=json.dumps(goal_data),
                              content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'ya existe' in data['error'].lower()
    
    # ==================== GET ALL ====================
    
    @patch('src.entities.salesperson_goal.IntegrationService')
    def test_get_goals_all(self, mock_integration, client, sample_salesperson_goal):
        """Test GET /salesperson-goals/ - get all goals."""
        # Mock IntegrationService for to_dict
        mock_service = MagicMock()
        mock_service.get_product_by_sku.return_value = {
            'sku': 'JER-001',
            'name': 'Jeringa 3ml',
            'description': 'Test description',
            'is_active': True,
            'unit_price': 0.35
        }
        mock_integration.return_value = mock_service
        
        response = client.get('/salesperson-goals/')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'goals' in data
        assert 'total' in data
        assert data['total'] >= 1
        assert isinstance(data['goals'], list)
        
        # Check first goal structure
        goal = data['goals'][0]
        assert 'id' in goal
        assert 'id_vendedor' in goal
        assert 'id_producto' in goal
        assert 'region' in goal
        assert 'trimestre' in goal
        assert 'valor_objetivo' in goal
        assert 'tipo' in goal
        assert 'vendedor' in goal
        assert 'producto' in goal
    
    @patch('src.entities.salesperson_goal.IntegrationService')
    def test_get_goals_filter_by_vendedor(self, mock_integration, client, multiple_salesperson_goals):
        """Test GET /salesperson-goals/ - filter by salesperson."""
        mock_service = MagicMock()
        mock_service.get_product_by_sku.return_value = {
            'sku': 'JER-001',
            'name': 'Jeringa 3ml',
            'description': 'Test',
            'is_active': True,
            'unit_price': 0.35
        }
        mock_integration.return_value = mock_service
        
        employee_id = multiple_salesperson_goals[0].id_vendedor
        response = client.get(f'/salesperson-goals/?id_vendedor={employee_id}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert all(goal['id_vendedor'] == employee_id for goal in data['goals'])
    
    @patch('src.entities.salesperson_goal.IntegrationService')
    def test_get_goals_filter_by_producto(self, mock_integration, client, multiple_salesperson_goals):
        """Test GET /salesperson-goals/ - filter by product."""
        mock_service = MagicMock()
        mock_service.get_product_by_sku.return_value = {
            'sku': 'JER-001',
            'name': 'Jeringa 3ml',
            'description': 'Test',
            'is_active': True,
            'unit_price': 0.35
        }
        mock_integration.return_value = mock_service
        
        product_sku = 'JER-001'
        response = client.get(f'/salesperson-goals/?id_producto={product_sku}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert all(goal['id_producto'] == product_sku for goal in data['goals'])
    
    @patch('src.entities.salesperson_goal.IntegrationService')
    def test_get_goals_filter_by_region(self, mock_integration, client, multiple_salesperson_goals):
        """Test GET /salesperson-goals/ - filter by region."""
        mock_service = MagicMock()
        mock_service.get_product_by_sku.return_value = {
            'sku': 'JER-001',
            'name': 'Jeringa 3ml',
            'description': 'Test',
            'is_active': True,
            'unit_price': 0.35
        }
        mock_integration.return_value = mock_service
        
        region = Region.NORTE.value
        response = client.get(f'/salesperson-goals/?region={region}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert all(goal['region'] == region for goal in data['goals'])
    
    @patch('src.entities.salesperson_goal.IntegrationService')
    def test_get_goals_filter_by_trimestre(self, mock_integration, client, multiple_salesperson_goals):
        """Test GET /salesperson-goals/ - filter by quarter."""
        mock_service = MagicMock()
        mock_service.get_product_by_sku.return_value = {
            'sku': 'JER-001',
            'name': 'Jeringa 3ml',
            'description': 'Test',
            'is_active': True,
            'unit_price': 0.35
        }
        mock_integration.return_value = mock_service
        
        trimestre = Quarter.Q1.value
        response = client.get(f'/salesperson-goals/?trimestre={trimestre}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert all(goal['trimestre'] == trimestre for goal in data['goals'])
    
    @patch('src.entities.salesperson_goal.IntegrationService')
    def test_get_goals_filter_by_tipo(self, mock_integration, client, multiple_salesperson_goals):
        """Test GET /salesperson-goals/ - filter by goal type."""
        mock_service = MagicMock()
        mock_service.get_product_by_sku.return_value = {
            'sku': 'JER-001',
            'name': 'Jeringa 3ml',
            'description': 'Test',
            'is_active': True,
            'unit_price': 0.35
        }
        mock_integration.return_value = mock_service
        
        tipo = GoalType.MONETARIO.value
        response = client.get(f'/salesperson-goals/?tipo={tipo}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert all(goal['tipo'] == tipo for goal in data['goals'])
    
    # ==================== GET BY ID ====================
    
    @patch('src.entities.salesperson_goal.IntegrationService')
    def test_get_goal_by_id(self, mock_integration, client, sample_salesperson_goal):
        """Test GET /salesperson-goals/<id> - retrieve single goal."""
        mock_service = MagicMock()
        mock_service.get_product_by_sku.return_value = {
            'sku': 'JER-001',
            'name': 'Jeringa 3ml',
            'description': 'Test',
            'is_active': True,
            'unit_price': 0.35
        }
        mock_integration.return_value = mock_service
        
        response = client.get(f'/salesperson-goals/{sample_salesperson_goal.id}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['id'] == sample_salesperson_goal.id
        assert data['id_vendedor'] == sample_salesperson_goal.id_vendedor
        assert data['id_producto'] == sample_salesperson_goal.id_producto
        assert data['region'] == sample_salesperson_goal.region
        assert data['trimestre'] == sample_salesperson_goal.trimestre
        assert data['valor_objetivo'] == float(sample_salesperson_goal.valor_objetivo)
        assert data['tipo'] == sample_salesperson_goal.tipo
        assert 'vendedor' in data
        assert 'producto' in data
    
    def test_get_goal_by_id_not_found(self, client):
        """Test GET /salesperson-goals/<id> - goal not found."""
        response = client.get('/salesperson-goals/99999')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
    
    # ==================== UPDATE (PUT) ====================
    
    @patch('src.entities.salesperson_goal.IntegrationService')
    def test_update_goal_success(self, mock_integration, client, sample_salesperson_goal):
        """Test PUT /salesperson-goals/<id> - update goal successfully."""
        mock_service = MagicMock()
        mock_service.get_product_by_sku.return_value = {
            'sku': 'JER-001',
            'name': 'Jeringa 3ml',
            'description': 'Test',
            'is_active': True,
            'unit_price': 0.35
        }
        mock_integration.return_value = mock_service
        
        update_data = {
            'valor_objetivo': 75000.00
        }
        
        response = client.put(f'/salesperson-goals/{sample_salesperson_goal.id}',
                             data=json.dumps(update_data),
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'goal' in data
        assert 'message' in data
        assert data['goal']['valor_objetivo'] == 75000.00
    
    def test_update_goal_not_found(self, client):
        """Test PUT /salesperson-goals/<id> - goal not found."""
        update_data = {
            'valor_objetivo': 75000.00
        }
        
        response = client.put('/salesperson-goals/99999',
                             data=json.dumps(update_data),
                             content_type='application/json')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_update_goal_no_json(self, client, sample_salesperson_goal):
        """Test PUT /salesperson-goals/<id> - no JSON provided."""
        response = client.put(f'/salesperson-goals/{sample_salesperson_goal.id}')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'No se proporcionó ningún dato' in data['error']
    
    @patch('src.entities.salesperson_goal.IntegrationService')
    def test_update_goal_invalid_region(self, mock_integration, client, sample_salesperson_goal):
        """Test PUT /salesperson-goals/<id> - invalid region."""
        update_data = {
            'region': 'InvalidRegion'
        }
        
        response = client.put(f'/salesperson-goals/{sample_salesperson_goal.id}',
                             data=json.dumps(update_data),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    # ==================== DELETE ====================
    
    @patch('src.entities.salesperson_goal.IntegrationService')
    def test_delete_goal_success(self, mock_integration, client, sample_salesperson_goal):
        """Test DELETE /salesperson-goals/<id> - delete goal successfully."""
        mock_service = MagicMock()
        mock_service.get_product_by_sku.return_value = {
            'sku': 'JER-001',
            'name': 'Jeringa 3ml',
            'description': 'Test',
            'is_active': True,
            'unit_price': 0.35
        }
        mock_integration.return_value = mock_service
        
        goal_id = sample_salesperson_goal.id
        response = client.delete(f'/salesperson-goals/{goal_id}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'message' in data
        assert 'deleted_goal' in data
        
        # Verify goal was deleted
        response = client.get(f'/salesperson-goals/{goal_id}')
        assert response.status_code == 404
    
    def test_delete_goal_not_found(self, client):
        """Test DELETE /salesperson-goals/<id> - goal not found."""
        response = client.delete('/salesperson-goals/99999')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
    
    # ==================== SPECIAL ENDPOINTS ====================
    
    @patch('src.entities.salesperson_goal.IntegrationService')
    def test_get_goals_by_salesperson(self, mock_integration, client, multiple_salesperson_goals):
        """Test GET /salesperson-goals/vendedor/<employee_id>."""
        mock_service = MagicMock()
        mock_service.get_product_by_sku.return_value = {
            'sku': 'JER-001',
            'name': 'Jeringa 3ml',
            'description': 'Test',
            'is_active': True,
            'unit_price': 0.35
        }
        mock_integration.return_value = mock_service
        
        employee_id = multiple_salesperson_goals[0].id_vendedor
        response = client.get(f'/salesperson-goals/vendedor/{employee_id}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'employee_id' in data
        assert 'goals' in data
        assert 'total' in data
        assert data['employee_id'] == employee_id
        assert all(goal['id_vendedor'] == employee_id for goal in data['goals'])
    
    @patch('src.entities.salesperson_goal.IntegrationService')
    def test_get_goals_by_salesperson_with_filters(self, mock_integration, client, multiple_salesperson_goals):
        """Test GET /salesperson-goals/vendedor/<employee_id> with filters."""
        mock_service = MagicMock()
        mock_service.get_product_by_sku.return_value = {
            'sku': 'JER-001',
            'name': 'Jeringa 3ml',
            'description': 'Test',
            'is_active': True,
            'unit_price': 0.35
        }
        mock_integration.return_value = mock_service
        
        employee_id = multiple_salesperson_goals[0].id_vendedor
        trimestre = Quarter.Q1.value
        response = client.get(f'/salesperson-goals/vendedor/{employee_id}?trimestre={trimestre}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert all(goal['trimestre'] == trimestre for goal in data['goals'])
    
    @patch('src.entities.salesperson_goal.IntegrationService')
    def test_get_goals_by_product(self, mock_integration, client, multiple_salesperson_goals):
        """Test GET /salesperson-goals/producto/<product_sku>."""
        mock_service = MagicMock()
        mock_service.get_product_by_sku.return_value = {
            'sku': 'JER-001',
            'name': 'Jeringa 3ml',
            'description': 'Test',
            'is_active': True,
            'unit_price': 0.35
        }
        mock_integration.return_value = mock_service
        
        product_sku = 'JER-001'
        response = client.get(f'/salesperson-goals/producto/{product_sku}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'product_sku' in data
        assert 'goals' in data
        assert 'total' in data
        assert data['product_sku'] == product_sku
        assert all(goal['id_producto'] == product_sku for goal in data['goals'])
    
    @patch('src.entities.salesperson_goal.IntegrationService')
    def test_get_goals_by_product_with_filters(self, mock_integration, client, multiple_salesperson_goals):
        """Test GET /salesperson-goals/producto/<product_sku> with filters."""
        mock_service = MagicMock()
        mock_service.get_product_by_sku.return_value = {
            'sku': 'JER-001',
            'name': 'Jeringa 3ml',
            'description': 'Test',
            'is_active': True,
            'unit_price': 0.35
        }
        mock_integration.return_value = mock_service
        
        product_sku = 'JER-001'
        region = Region.NORTE.value
        response = client.get(f'/salesperson-goals/producto/{product_sku}?region={region}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert all(goal['region'] == region for goal in data['goals'])
    
    # ==================== PRODUCT ENRICHMENT TESTS ====================
    
    @patch('src.entities.salesperson_goal.IntegrationService')
    def test_product_enrichment_success(self, mock_integration, client, sample_salesperson_goal):
        """Test that product object is enriched with catalog data."""
        mock_service = MagicMock()
        mock_service.get_product_by_sku.return_value = {
            'sku': 'JER-001',
            'name': 'Jeringa desechable 3ml con aguja',
            'description': 'Jeringa estéril desechable de 3ml con aguja calibre 21G x 1½',
            'is_active': True,
            'unit_price': 0.35
        }
        mock_integration.return_value = mock_service
        
        response = client.get(f'/salesperson-goals/{sample_salesperson_goal.id}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'producto' in data
        assert data['producto']['sku'] == 'JER-001'
        assert data['producto']['name'] == 'Jeringa desechable 3ml con aguja'
        assert data['producto']['description'] is not None
        assert data['producto']['unit_price'] == 0.35
        assert data['producto']['is_active'] is True
    
    @patch('src.entities.salesperson_goal.IntegrationService')
    def test_product_enrichment_failure_graceful(self, mock_integration, client, sample_salesperson_goal):
        """Test graceful handling when catalog service fails."""
        mock_service = MagicMock()
        mock_service.get_product_by_sku.side_effect = Exception("Catalog service unavailable")
        mock_integration.return_value = mock_service
        
        response = client.get(f'/salesperson-goals/{sample_salesperson_goal.id}')
        
        # Should still return 200 but with partial product data
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'producto' in data
        assert data['producto']['sku'] == sample_salesperson_goal.id_producto
        assert data['producto']['name'] is None
        assert data['producto']['description'] is None
        assert data['producto']['unit_price'] is None
        assert data['producto']['is_active'] is None
