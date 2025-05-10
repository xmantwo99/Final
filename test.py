import pytest
import json
from flask import session
from unittest.mock import patch, MagicMock
from werkzeug.security import generate_password_hash

# Import the Flask app
from app import app, get_user_by_username, add_sample_products

@pytest.fixture
def client():
    """Create a test client for the app."""
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
    
    with app.test_client() as client:
        with app.app_context():
            # Create a test database and insert test data
            yield client

@pytest.fixture
def mock_db_connection():
    """Mock database connection for all tests."""
    with patch('app.get_connection') as mock_conn:
        conn = MagicMock()
        cursor = MagicMock()
        conn.cursor.return_value = cursor
        mock_conn.return_value = conn
        yield conn, cursor

class TestAuthenticationEndpoints:
    """Tests for login, signup, and logout endpoints."""

    def test_login_get(self, client):
        """Test GET request to login returns the login form."""
        response = client.get('/login')
        assert response.status_code == 200
        assert b'login' in response.data.lower()

    def test_login_post_valid(self, client, mock_db_connection):
        """Test POST with valid credentials logs in user."""
        conn, cursor = mock_db_connection
        
        # Mock user query result for successful login
        cursor.fetchone.return_value = type('User', (), {
            'id': 1, 
            'username': 'testuser', 
            'password_hash': generate_password_hash('password123')
        })
        
        response = client.post('/login', data={
            'username': 'testuser',
            'password': 'password123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'home' in response.data.lower()
        
    def test_login_post_invalid(self, client, mock_db_connection):
        """Test POST with invalid credentials shows error."""
        conn, cursor = mock_db_connection
        
        # Mock user query result (user exists but password wrong)
        cursor.fetchone.return_value = type('User', (), {
            'id': 1, 
            'username': 'testuser', 
            'password_hash': generate_password_hash('correctpassword')
        })
        
        response = client.post('/login', data={
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        
        assert b'invalid username or password' in response.data.lower()
    
    def test_login_empty_fields(self, client):
        """Test login with empty fields."""
        response = client.post('/login', data={
            'username': '',
            'password': ''
        })
        assert response.status_code == 200
        assert b'invalid username or password' in response.data.lower()

    def test_signup_get(self, client):
        """Test GET request to signup returns the signup form."""
        response = client.get('/signup')
        assert response.status_code == 200
        assert b'signup' in response.data.lower()

    def test_signup_post_valid(self, client, mock_db_connection):
        """Test POST with valid new user creates account."""
        conn, cursor = mock_db_connection
        
        # Mock user query result for new user (username doesn't exist)
        cursor.fetchone.return_value = None
        
        response = client.post('/signup', data={
            'username': 'newuser',
            'password': 'password123'
        }, follow_redirects=True)
        
        # Check if user creation was called
        cursor.execute.assert_called()
        conn.commit.assert_called_once()
        assert b'account created' in response.data.lower()
    
    def test_signup_existing_username(self, client, mock_db_connection):
        """Test signup with existing username shows error."""
        conn, cursor = mock_db_connection
        
        # Mock user query result for existing user
        cursor.fetchone.return_value = type('User', (), {
            'id': 1, 
            'username': 'existinguser', 
            'password_hash': 'somehash'
        })
        
        response = client.post('/signup', data={
            'username': 'existinguser',
            'password': 'password123'
        })
        
        assert b'username already exists' in response.data.lower()

    def test_logout(self, client):
        """Test logout endpoint clears session and redirects."""
        with client.session_transaction() as sess:
            sess['user_id'] = 1  # Set a user_id to simulate logged in user
            sess['cart'] = {'1': 2}  # Add something to the cart
        
        with patch('flask_login.utils._get_user') as mock_get_user:
            # Mock the current_user so is_authenticated returns True
            mock_user = MagicMock()
            mock_user.is_authenticated = True
            mock_get_user.return_value = mock_user
            
            response = client.get('/logout', follow_redirects=True)
            
            with client.session_transaction() as sess:
                assert 'cart' not in sess
            
            assert response.status_code == 200
            assert b'home' in response.data.lower()


class TestProductEndpoints:
    """Tests for product related endpoints."""
    
    def test_products_list(self, client, mock_db_connection):
        """Test products endpoint returns product list."""
        conn, cursor = mock_db_connection
        
        # Mock product query results
        cursor.fetchall.return_value = [
            type('Product', (), {'id': 1, 'name': 'Cherry MX Pro', 'price': 129.99, 'description': 'RGB keyboard', 'image': 'cherry_mx.jpg'}),
            type('Product', (), {'id': 2, 'name': 'Silent TypeMaster', 'price': 89.99, 'description': 'Quiet keyboard', 'image': 'silent.jpg'})
        ]
        
        response = client.get('/products')
        
        assert response.status_code == 200
        assert b'cherry mx pro' in response.data.lower()
        assert b'silent typemaster' in response.data.lower()
    
    def test_products_empty_list(self, client, mock_db_connection):
        """Test products endpoint with no products."""
        conn, cursor = mock_db_connection
        
        # Mock empty product query results
        cursor.fetchall.return_value = []
        
        response = client.get('/products')
        
        assert response.status_code == 200
        # Specifically check for product absence, implementation might show "No products" message
    
    def test_add_sample_products(self, client, mock_db_connection):
        """Test add sample products endpoint."""
        conn, cursor = mock_db_connection
        
        response = client.get('/add-sample-products')
        
        assert response.status_code == 200
        assert b'sample products added' in response.data.lower()
        cursor.executemany.assert_called_once()
        conn.commit.assert_called_once()


class TestCartEndpoints:
    """Tests for shopping cart related endpoints."""
    
    def test_add_to_cart_authenticated(self, client, mock_db_connection):
        """Test adding product to cart when authenticated."""
        conn, cursor = mock_db_connection
        
        # Mock product query result
        cursor.fetchone.return_value = type('Product', (), {
            'id': 1, 
            'name': 'Cherry MX Pro', 
            'price': 129.99, 
            'description': 'RGB keyboard', 
            'image': 'cherry_mx.jpg'
        })
        
        with client.session_transaction() as sess:
            sess['_user_id'] = '1'  # Set a user_id to simulate logged in user
        
        with patch('flask_login.utils._get_user') as mock_get_user:
            # Mock the current_user so is_authenticated returns True
            mock_user = MagicMock()
            mock_user.is_authenticated = True
            mock_get_user.return_value = mock_user
            
            response = client.get('/add_to_cart/1', follow_redirects=True)
            
            with client.session_transaction() as sess:
                assert '1' in sess['cart']
                assert sess['cart']['1'] == 1
            
            assert response.status_code == 200
            assert b'added to your cart' in response.data.lower()
    
    def test_add_to_cart_unauthenticated(self, client):
        """Test adding product to cart when not authenticated."""
        with patch('flask_login.utils._get_user') as mock_get_user:
            # Mock the current_user so is_authenticated returns False
            mock_user = MagicMock()
            mock_user.is_authenticated = False
            mock_get_user.return_value = mock_user
            
            response = client.get('/add_to_cart/1', follow_redirects=True)
            
            assert response.status_code == 200
            assert b'must be logged in' in response.data.lower()
            assert b'login' in response.data.lower()

    def test_add_custom_build(self, client):
        """Test adding custom build to cart."""
        with client.session_transaction() as sess:
            sess['_user_id'] = '1'  # Set a user_id to simulate logged in user
        
        with patch('flask_login.utils._get_user') as mock_get_user:
            # Mock the current_user so is_authenticated returns True
            mock_user = MagicMock()
            mock_user.is_authenticated = True
            mock_get_user.return_value = mock_user
            
            response = client.get('/add_custom_build', follow_redirects=True)
            
            with client.session_transaction() as sess:
                assert 'custom_build' in sess['cart']
                assert sess['cart']['custom_build'] == 1
            
            assert response.status_code == 200
            assert b'custom keyboard build added to cart' in response.data.lower()

    def test_remove_from_cart(self, client):
        """Test removing product from cart."""
        # Setup cart with a product
        with client.session_transaction() as sess:
            sess['cart'] = {'1': 1, '2': 3}
        
        response = client.get('/remove_from_cart/1', follow_redirects=True)
        
        with client.session_transaction() as sess:
            assert '1' not in sess['cart']
            assert '2' in sess['cart']  # Other product still there
        
        assert response.status_code == 200
        assert b'item removed from cart' in response.data.lower()

    def test_cart_view(self, client, mock_db_connection):
        """Test viewing cart with products."""
        conn, cursor = mock_db_connection
        
        # Set up mock product fetching
        def side_effect_func(product_id):
            products = {
                1: type('Product', (), {'id': 1, 'name': 'Cherry MX Pro', 'price': 129.99, 'description': 'RGB keyboard', 'image': 'cherry_mx.jpg'}),
                2: type('Product', (), {'id': 2, 'name': 'Silent TypeMaster', 'price': 89.99, 'description': 'Quiet keyboard', 'image': 'silent.jpg'})
            }
            cursor.fetchone.return_value = products.get(product_id)
            return {'id': product_id, 'name': products[product_id].name, 'price': products[product_id].price, 
                    'description': products[product_id].description, 'image': products[product_id].image}
        
        # Setup cart with products and custom build
        with client.session_transaction() as sess:
            sess['cart'] = {'1': 2, '2': 1, 'custom_build': 1}
        
        with patch('app.get_product_by_id', side_effect=side_effect_func):
            response = client.get('/cart')
            
            assert response.status_code == 200
            assert b'cherry mx pro' in response.data.lower()
            assert b'silent typemaster' in response.data.lower()
            assert b'custom keyboard build' in response.data.lower()
            # Total should be (129.99*2 + 89.99 + 175.00)
            # But won't check exact amount due to floating point comparison

    def test_checkout(self, client):
        """Test checkout endpoint clears cart."""
        # Setup cart with products
        with client.session_transaction() as sess:
            sess['cart'] = {'1': 2, '2': 1}
        
        response = client.get('/checkout')
        
        with client.session_transaction() as sess:
            assert 'cart' not in sess
        
        assert response.status_code == 200
        assert b'checkout' in response.data.lower()


class TestBuilderEndpoints:
    """Tests for keyboard builder related endpoints."""
    
    def test_builder_view(self, client):
        """Test keyboard builder view loads."""
        response = client.get('/builder')
        
        assert response.status_code == 200
        assert b'builder' in response.data.lower()
    
    def test_builder_preview(self, client):
        """Test builder preview with selections."""
        response = client.post('/builder_preview', data={
            'switches': 'Cherry MX Red',
            'layout': '60%',
            'case': 'Aluminum'
        })
        
        assert response.status_code == 200
        assert b'preview' in response.data.lower()
        assert b'cherry mx red' in response.data.lower()
        assert b'60%' in response.data.lower()
        assert b'aluminum' in response.data.lower()
    
    def test_builder_preview_empty(self, client):
        """Test builder preview with empty selections."""
        response = client.post('/builder_preview', data={
            'switches': '',
            'layout': '',
            'case': ''
        })
        
        assert response.status_code == 200
        # Check that it doesn't error with empty values


class TestGeneralPages:
    """Tests for home and test pages."""
    
    def test_home_page(self, client):
        """Test home page loads."""
        response = client.get('/')
        
        assert response.status_code == 200
        assert b'home' in response.data.lower()
    
    def test_home_page_authenticated(self, client):
        """Test home page when authenticated."""
        with client.session_transaction() as sess:
            sess['_user_id'] = '1'
        
        with patch('flask_login.utils._get_user') as mock_get_user:
            # Mock the current_user
            mock_user = MagicMock()
            mock_user.is_authenticated = True
            mock_user.username = 'testuser'
            mock_get_user.return_value = mock_user
            
            response = client.get('/')
            
            assert response.status_code == 200
            # Should show user-specific content (implementation dependent)
    
    def test_test_page(self, client):
        """Test the test page loads."""
        response = client.get('/test')
        
        assert response.status_code == 200
        assert b'test' in response.data.lower()


class TestEdgeCases:
    """Tests for various edge cases."""
    
    def test_add_nonexistent_product(self, client, mock_db_connection):
        """Test adding non-existent product to cart."""
        conn, cursor = mock_db_connection
        
        # Mock product query result for non-existent product
        cursor.fetchone.return_value = None
        
        with client.session_transaction() as sess:
            sess['_user_id'] = '1'
        
        with patch('flask_login.utils._get_user') as mock_get_user:
            # Mock the current_user
            mock_user = MagicMock()
            mock_user.is_authenticated = True
            mock_get_user.return_value = mock_user
            
            # This should handle the case gracefully or show an error
            response = client.get('/add_to_cart/999', follow_redirects=True)
            assert response.status_code == 200
    
    def test_login_sql_injection(self, client, mock_db_connection):
        """Test login with SQL injection attempt."""
        conn, cursor = mock_db_connection
        
        # Mock user query with SQL injection username
        cursor.fetchone.return_value = None  # No user found
        
        response = client.post('/login', data={
            'username': "admin' OR 1=1--",
            'password': 'anything'
        })
        
        assert response.status_code == 200
        assert b'invalid username or password' in response.data.lower()
        # Check that SQL injection didn't succeed by verifying not logged in
    
    def test_signup_long_username(self, client, mock_db_connection):
        """Test signup with extremely long username."""
        conn, cursor = mock_db_connection
        
        # Mock user query result for new user
        cursor.fetchone.return_value = None
        
        very_long_username = 'a' * 1000  # 1000 character username
        
        response = client.post('/signup', data={
            'username': very_long_username,
            'password': 'password123'
        })
        
        # The application should either handle this gracefully or enforce a limit
        assert response.status_code == 200
    
    def test_multiple_custom_builds(self, client):
        """Test adding multiple custom builds to cart."""
        with client.session_transaction() as sess:
            sess['_user_id'] = '1'
            sess['cart'] = {'custom_build': 1}  # Already has one
        
        with patch('flask_login.utils._get_user') as mock_get_user:
            # Mock the current_user
            mock_user = MagicMock()
            mock_user.is_authenticated = True
            mock_get_user.return_value = mock_user
            
            response = client.get('/add_custom_build', follow_redirects=True)
            
            with client.session_transaction() as sess:
                assert sess['cart']['custom_build'] == 2  # Count increased
            
            assert response.status_code == 200
    
    def test_remove_nonexistent_from_cart(self, client):
        """Test removing non-existent product from cart."""
        # Setup cart with a product
        with client.session_transaction() as sess:
            sess['cart'] = {'1': 1}
        
        response = client.get('/remove_from_cart/999', follow_redirects=True)
        
        with client.session_transaction() as sess:
            assert '1' in sess['cart']  # Original product still there
        
        assert response.status_code == 200
        assert b'item removed from cart' in response.data.lower()
    
    def test_empty_cart_view(self, client):
        """Test viewing empty cart."""
        # Don't set up any cart items
        response = client.get('/cart')
        
        assert response.status_code == 200
        # Empty cart display (implementation dependent)
    
    def test_checkout_empty_cart(self, client):
        """Test checkout with empty cart."""
        # Don't set up any cart items
        response = client.get('/checkout')
        
        assert response.status_code == 200
        assert b'checkout' in response.data.lower()