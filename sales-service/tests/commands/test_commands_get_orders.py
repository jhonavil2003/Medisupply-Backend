from src.commands.get_orders import GetOrders


class TestGetOrdersCommand:
    
    def test_get_all_orders(self, db, sample_order):
        """Test getting all orders."""
        command = GetOrders()
        result = command.execute()
        
        assert len(result) >= 1
        assert result[0]['order_number'] == sample_order.order_number
    
    def test_get_orders_includes_items(self, db, sample_order):
        """Test that orders include items."""
        command = GetOrders()
        result = command.execute()
        
        assert 'items' in result[0]
        assert len(result[0]['items']) >= 2
    
    def test_get_orders_includes_customer(self, db, sample_order, sample_customer):
        """Test that orders include complete customer object."""
        command = GetOrders()
        result = command.execute()
        
        assert len(result) >= 1
        order = result[0]
        
        # Verify customer object is present
        assert 'customer' in order
        assert order['customer'] is not None
        
        # Verify customer has all required fields
        customer = order['customer']
        assert 'id' in customer
        assert 'business_name' in customer
        assert 'trade_name' in customer
        assert 'document_number' in customer
        assert customer['id'] == sample_customer.id
        assert customer['business_name'] == sample_customer.business_name
    
    def test_get_orders_by_customer(self, db, sample_order, sample_customer):
        """Test filtering orders by customer."""
        command = GetOrders(customer_id=sample_customer.id)
        result = command.execute()
        
        assert len(result) >= 1
        assert all(o['customer_id'] == sample_customer.id for o in result)
    
    def test_get_orders_by_seller(self, db, sample_order):
        """Test filtering orders by seller."""
        command = GetOrders(seller_id='SELLER-001')
        result = command.execute()
        
        assert len(result) >= 1
        assert all(o['seller_id'] == 'SELLER-001' for o in result)
    
    def test_get_orders_by_status(self, db, sample_order):
        """Test filtering orders by status."""
        command = GetOrders(status='pending')
        result = command.execute()
        
        assert len(result) >= 1
        assert all(o['status'] == 'pending' for o in result)
    
    def test_get_orders_combined_filters(self, db, sample_order, sample_customer):
        """Test combining multiple filters."""
        command = GetOrders(customer_id=sample_customer.id, status='pending')
        result = command.execute()
        
        assert len(result) >= 1
        order = result[0]
        assert order['customer_id'] == sample_customer.id
        assert order['status'] == 'pending'
    
    def test_get_orders_ordered_by_date_desc(self, db, multiple_orders):
        """Test that orders are ordered by date descending."""
        command = GetOrders()
        result = command.execute()
        
        # Should have at least 2 orders from multiple_orders fixture
        assert len(result) >= 2
        # More recent orders should come first
        for i in range(len(result) - 1):
            assert result[i]['order_date'] >= result[i + 1]['order_date']
    
    def test_get_orders_no_results(self, db):
        """Test getting orders with no results."""
        command = GetOrders(status='nonexistent_status')
        result = command.execute()
        
        assert len(result) == 0
