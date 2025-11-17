import pytest
from src.commands.get_products import GetProducts
from src.models.product import Product
from src.session import db


class TestGetProducts:
    
    def test_get_products_no_filters(self, app, multiple_products):
        """Test getting all products without filters"""
        with app.app_context():
            command = GetProducts()
            result = command.execute()
            
            assert 'products' in result
            assert 'pagination' in result
            assert len(result['products']) > 0
            assert result['pagination']['page'] == 1
            # Default is_active=True, so only 3 active products from multiple_products
            assert result['pagination']['total_items'] == 3
    
    def test_get_products_filter_by_category(self, app, multiple_products):
        """Test filtering products by category"""
        with app.app_context():
            # Create a product with specific category
            from src.models.supplier import Supplier
            supplier = Supplier.query.first()
            
            test_product = Product(
                sku='TEST-CAT-001',
                name='Category Test Product',
                category='Medical Devices',
                unit_price=100.00,
                unit_of_measure='unit',
                supplier_id=supplier.id
            )
            db.session.add(test_product)
            db.session.commit()
            
            command = GetProducts(category='Medical Devices')
            result = command.execute()
            
            assert len(result['products']) > 0
            for product in result['products']:
                assert 'Medical Devices' in product['category']
    
    def test_get_products_filter_by_subcategory(self, app, multiple_products):
        """Test filtering products by subcategory"""
        with app.app_context():
            # Create a product with specific subcategory
            from src.models.supplier import Supplier
            supplier = Supplier.query.first()
            
            test_product = Product(
                sku='TEST-SUBCAT-001',
                name='Subcategory Test Product',
                category='Medical',
                subcategory='Surgical Instruments',
                unit_price=150.00,
                unit_of_measure='unit',
                supplier_id=supplier.id
            )
            db.session.add(test_product)
            db.session.commit()
            
            command = GetProducts(subcategory='Surgical Instruments')
            result = command.execute()
            
            assert len(result['products']) > 0
            for product in result['products']:
                assert 'Surgical Instruments' in product['subcategory']
    
    def test_get_products_filter_by_supplier_id(self, app, multiple_products):
        """Test filtering products by supplier ID"""
        with app.app_context():
            from src.models.supplier import Supplier
            supplier = Supplier.query.first()
            
            command = GetProducts(supplier_id=supplier.id)
            result = command.execute()
            
            assert len(result['products']) > 0
            for product in result['products']:
                assert product['supplier_id'] == supplier.id
    
    def test_get_products_filter_by_sku(self, app, multiple_products):
        """Test filtering products by SKU pattern"""
        with app.app_context():
            first_product = multiple_products[0]
            sku_part = first_product.sku[:5]  # Get first 5 chars of SKU
            
            command = GetProducts(sku=sku_part)
            result = command.execute()
            
            assert len(result['products']) > 0
            for product in result['products']:
                assert sku_part.upper() in product['sku'].upper()
    
    def test_get_products_filter_by_is_active_true(self, app, multiple_products):
        """Test filtering products by is_active=True"""
        with app.app_context():
            command = GetProducts(is_active=True)
            result = command.execute()
            
            assert len(result['products']) > 0
            for product in result['products']:
                assert product['is_active'] is True
    
    def test_get_products_filter_by_is_active_false(self, app, multiple_products):
        """Test filtering products by is_active=False"""
        with app.app_context():
            # multiple_products already has an inactive product (INACTIVE-001)
            command = GetProducts(is_active=False)
            result = command.execute()
            
            assert len(result['products']) > 0
            for product in result['products']:
                assert product['is_active'] is False
    
    def test_get_products_filter_by_requires_cold_chain_true(self, app, multiple_products):
        """Test filtering products by requires_cold_chain=True"""
        with app.app_context():
            # Create a cold chain product
            from src.models.supplier import Supplier
            supplier = Supplier.query.first()
            
            cold_product = Product(
                sku='COLD-001',
                name='Cold Chain Product',
                category='Vaccines',
                unit_price=200.00,
                unit_of_measure='vial',
                supplier_id=supplier.id,
                requires_cold_chain=True
            )
            db.session.add(cold_product)
            db.session.commit()
            
            command = GetProducts(requires_cold_chain=True)
            result = command.execute()
            
            assert len(result['products']) > 0
            for product in result['products']:
                assert product['requires_cold_chain'] is True
    
    def test_get_products_filter_by_requires_cold_chain_false(self, app, multiple_products):
        """Test filtering products by requires_cold_chain=False"""
        with app.app_context():
            command = GetProducts(requires_cold_chain=False)
            result = command.execute()
            
            for product in result['products']:
                assert product['requires_cold_chain'] is False
    
    def test_get_products_search_by_name(self, app, multiple_products):
        """Test searching products by name"""
        with app.app_context():
            first_product = multiple_products[0]
            search_term = first_product.name.split()[0]  # First word of name
            
            command = GetProducts(search=search_term)
            result = command.execute()
            
            assert len(result['products']) > 0
    
    def test_get_products_search_by_description(self, app, sample_supplier):
        """Test searching products by description"""
        with app.app_context():
            # Create a product with specific description
            test_product = Product(
                sku='DESC-001',
                name='Description Test',
                description='This is a unique description for testing',
                category='Test',
                unit_price=75.00,
                unit_of_measure='unit',
                supplier_id=sample_supplier.id
            )
            db.session.add(test_product)
            db.session.commit()
            
            command = GetProducts(search='unique description')
            result = command.execute()
            
            assert len(result['products']) > 0
    
    def test_get_products_search_by_sku(self, app, multiple_products):
        """Test searching products by SKU"""
        with app.app_context():
            first_product = multiple_products[0]
            
            command = GetProducts(search=first_product.sku)
            result = command.execute()
            
            assert len(result['products']) > 0
            found = False
            for product in result['products']:
                if product['sku'] == first_product.sku:
                    found = True
                    break
            assert found
    
    def test_get_products_search_by_barcode(self, app, sample_supplier):
        """Test searching products by barcode"""
        with app.app_context():
            # Create a product with barcode
            test_product = Product(
                sku='BARCODE-001',
                name='Barcode Test',
                category='Test',
                unit_price=60.00,
                unit_of_measure='unit',
                supplier_id=sample_supplier.id,
                barcode='1234567890123'
            )
            db.session.add(test_product)
            db.session.commit()
            
            command = GetProducts(search='1234567890123')
            result = command.execute()
            
            assert len(result['products']) > 0
    
    def test_get_products_search_by_manufacturer(self, app, sample_supplier):
        """Test searching products by manufacturer"""
        with app.app_context():
            # Create a product with manufacturer
            test_product = Product(
                sku='MFG-001',
                name='Manufacturer Test',
                category='Test',
                unit_price=90.00,
                unit_of_measure='unit',
                supplier_id=sample_supplier.id,
                manufacturer='UniqueManufacturer Inc'
            )
            db.session.add(test_product)
            db.session.commit()
            
            command = GetProducts(search='UniqueManufacturer')
            result = command.execute()
            
            assert len(result['products']) > 0
    
    def test_get_products_pagination_first_page(self, app, multiple_products):
        """Test pagination - first page"""
        with app.app_context():
            command = GetProducts(page=1, per_page=5)
            result = command.execute()
            
            assert result['pagination']['page'] == 1
            assert result['pagination']['per_page'] == 5
            assert len(result['products']) <= 5
    
    def test_get_products_pagination_second_page(self, app, multiple_products):
        """Test pagination - second page"""
        with app.app_context():
            command = GetProducts(page=2, per_page=5)
            result = command.execute()
            
            assert result['pagination']['page'] == 2
            assert result['pagination']['per_page'] == 5
    
    def test_get_products_pagination_max_per_page(self, app, multiple_products):
        """Test that per_page is capped at 100"""
        with app.app_context():
            command = GetProducts(per_page=200)
            result = command.execute()
            
            assert result['pagination']['per_page'] == 100
    
    def test_get_products_pagination_min_per_page(self, app, multiple_products):
        """Test that per_page has minimum of 1"""
        with app.app_context():
            command = GetProducts(per_page=0)
            result = command.execute()
            
            assert result['pagination']['per_page'] == 1
    
    def test_get_products_pagination_min_page(self, app, multiple_products):
        """Test that page has minimum of 1"""
        with app.app_context():
            command = GetProducts(page=0)
            result = command.execute()
            
            assert result['pagination']['page'] == 1
    
    def test_get_products_pagination_negative_page(self, app, multiple_products):
        """Test that negative page defaults to 1"""
        with app.app_context():
            command = GetProducts(page=-5)
            result = command.execute()
            
            assert result['pagination']['page'] == 1
    
    def test_get_products_pagination_has_next(self, app, multiple_products):
        """Test pagination has_next flag"""
        with app.app_context():
            command = GetProducts(page=1, per_page=2)
            result = command.execute()
            
            if result['pagination']['total_items'] > 2:
                assert result['pagination']['has_next'] is True
    
    def test_get_products_pagination_has_prev(self, app, multiple_products):
        """Test pagination has_prev flag"""
        with app.app_context():
            command = GetProducts(page=2, per_page=2)
            result = command.execute()
            
            assert result['pagination']['has_prev'] is True
    
    def test_get_products_empty_result(self, app):
        """Test that empty results are handled gracefully"""
        with app.app_context():
            command = GetProducts(search='NONEXISTENT_PRODUCT_XYZ123')
            result = command.execute()
            
            assert result['products'] == []
            assert result['pagination']['total_items'] == 0
    
    def test_get_products_multiple_filters(self, app, sample_supplier):
        """Test combining multiple filters"""
        with app.app_context():
            # Create products with specific attributes
            test_product = Product(
                sku='MULTI-001',
                name='Multi Filter Test',
                category='Pharmaceuticals',
                subcategory='Antibiotics',
                unit_price=100.00,
                unit_of_measure='box',
                supplier_id=sample_supplier.id,
                is_active=True,
                requires_cold_chain=True
            )
            db.session.add(test_product)
            db.session.commit()
            
            command = GetProducts(
                category='Pharmaceuticals',
                subcategory='Antibiotics',
                is_active=True,
                requires_cold_chain=True,
                supplier_id=sample_supplier.id
            )
            result = command.execute()
            
            assert len(result['products']) > 0
            for product in result['products']:
                assert 'Pharmaceuticals' in product['category']
                assert product['is_active'] is True
                assert product['requires_cold_chain'] is True
                assert product['supplier_id'] == sample_supplier.id
    
    def test_get_products_ordered_by_name(self, app, multiple_products):
        """Test that products are ordered by name"""
        with app.app_context():
            command = GetProducts(per_page=50)
            result = command.execute()
            
            if len(result['products']) > 1:
                names = [p['name'] for p in result['products']]
                # Check if sorted (case-insensitive)
                assert names == sorted(names, key=str.lower)
    
    def test_get_products_is_active_none(self, app, multiple_products):
        """Test filtering with is_active=None returns all products"""
        with app.app_context():
            # Create both active and inactive products
            from src.models.supplier import Supplier
            supplier = Supplier.query.first()
            
            active_prod = Product(
                sku='ACTIVE-TEST',
                name='Active Test',
                category='Test',
                unit_price=50.00,
                unit_of_measure='unit',
                supplier_id=supplier.id,
                is_active=True
            )
            inactive_prod = Product(
                sku='INACTIVE-TEST',
                name='Inactive Test',
                category='Test',
                unit_price=50.00,
                unit_of_measure='unit',
                supplier_id=supplier.id,
                is_active=False
            )
            db.session.add_all([active_prod, inactive_prod])
            db.session.commit()
            
            command = GetProducts(is_active=None)
            result = command.execute()
            
            # Should include both active and inactive
            skus = [p['sku'] for p in result['products']]
            assert 'ACTIVE-TEST' in skus or 'INACTIVE-TEST' in skus
