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
        """Ensures the login page loads correctly."""
        response = client.get('/login')
        assert response.status_code == 200
        assert b'login' in response.data.lower()

    def test_login_post_valid(self, client, mock_db_connection):
        """Verifies that a user can log in with valid credentials."""
        conn, cursor = mock_db_connection

        # Simulate a user existing in the database
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
        with client.session_transaction() as sess:
            assert 'user_id' in sess

    def test_login_post_invalid(self, client, mock_db_connection):
        """Checks that an error message is displayed for incorrect password."""
        conn, cursor = mock_db_connection

        # Simulate a user existing but with a different password
        cursor.fetchone.return_value = type('User', (), {
            'id': 1,
            'username': 'testuser',
            'password_hash': generate_password_hash('correctpassword')
        })

        response = client.post('/login', data={
            'username': 'testuser',
            'password': 'wrongpassword'
        })

        assert response.status_code == 200
        assert b'invalid username or password' in response.data.lower()
        with client.session_transaction() as sess:
            assert 'user_id' not in sess

    def test_login_empty_fields(self, client):
        """Confirms that submitting empty login fields shows an error."""
        response = client.post('/login', data={
            'username': '',
            'password': ''
        })
        assert response.status_code == 200
        assert b'invalid username or password' in response.data.lower()
        with client.session_transaction() as sess:
            assert 'user_id' not in sess

    def test_signup_get(self, client):
        """Verifies the signup page loads."""
        response = client.get('/signup')
        assert response.status_code == 200
        assert b'signup' in response.data.lower()

    def test_signup_post_valid(self, client, mock_db_connection):
        """Ensures a new user account can be created."""
        conn, cursor = mock_db_connection

        # Simulate no existing user with the new username
        cursor.fetchone.return_value = None

        response = client.post('/signup', data={
            'username': 'newuser',
            'password': 'password123'
        }, follow_redirects=True)

        # Check if the database insert operation was called
        cursor.execute.assert_called()
        conn.commit.assert_called_once()
        assert response.status_code == 200
        assert b'account created' in response.data.lower()
        with client.session_transaction() as sess:
            assert 'user_id' in sess

    def test_signup_existing_username(self, client, mock_db_connection):
        """Checks that an error is shown if the chosen username already exists."""
        conn, cursor = mock_db_connection

        # Simulate a user already existing with the given username
        cursor.fetchone.return_value = type('User', (), {
            'id': 1,
            'username': 'existinguser',
            'password_hash': 'somehash'
        })

        response = client.post('/signup', data={
            'username': 'existinguser',
            'password': 'password123'
        })

        assert response.status_code == 200
        assert b'username already exists' in response.data.lower()
        with client.session_transaction() as sess:
            assert 'user_id' not in sess

    def test_logout(self, client):
        """Verifies that logout clears the session and redirects to the home page."""
        with client.session_transaction() as sess:
            sess['user_id'] = 1  # Simulate a logged-in user
            sess['cart'] = {'1': 2}  # Simulate items in the cart

        with patch('flask_login.utils._get_user') as mock_get_user:
            # Mock the current_user to simulate an authenticated user
            mock_user = MagicMock()
            mock_user.is_authenticated = True
            mock_get_user.return_value = mock_user

            response = client.get('/logout', follow_redirects=True)

            with client.session_transaction() as sess:
                assert 'user_id' not in sess
                assert 'cart' not in sess # Ensure cart is cleared upon logout

            assert response.status_code == 200
            assert b'home' in response.data.lower()


class TestProductEndpoints:
    """Tests for product related endpoints."""

    def test_products_list(self, client, mock_db_connection):
        """Ensures the products page displays a list of products."""
        conn, cursor = mock_db_connection

        # Simulate fetching a list of products from the database
        cursor.fetchall.return_value = [
            type('Product', (), {'id': 1, 'name': 'Cherry MX Pro', 'price': 129.99, 'description': 'RGB keyboard', 'image': 'cherry_mx.jpg'}),
            type('Product', (), {'id': 2, 'name': 'Silent TypeMaster', 'price': 89.99, 'description': 'Quiet keyboard', 'image': 'silent.jpg'})
        ]

        response = client.get('/products')

        assert response.status_code == 200
        assert b'cherry mx pro' in response.data.lower()
        assert b'silent typemaster' in response.data.lower()

    def test_products_empty_list(self, client, mock_db_connection):
        """Checks that the products page handles an empty product list gracefully."""
        conn, cursor = mock_db_connection

        # Simulate no products in the database
        cursor.fetchall.return_value = []

        response = client.get('/products')

        assert response.status_code == 200
        assert b'no products available' in response.data.lower() or b'no products found' in response.data.lower() # Check for a message indicating no products

    def test_add_sample_products(self, client, mock_db_connection):
        """Verifies the functionality of adding sample products."""
        conn, cursor = mock_db_connection

        response = client.get('/add-sample-products')

        assert response.status_code == 200
        assert b'sample products added' in response.data.lower()
        cursor.executemany.assert_called_once() # Check if the bulk insert was called
        conn.commit.assert_called_once() # Check if changes were committed


class TestCartEndpoints:
    """Tests for shopping cart related endpoints."""

    def test_add_to_cart_authenticated(self, client, mock_db_connection):
        """Ensures an authenticated user can add a product to their cart."""
        conn, cursor = mock_db_connection

        # Simulate fetching a product from the database
        cursor.fetchone.return_value = type('Product', (), {
            'id': 1,
            'name': 'Cherry MX Pro',
            'price': 129.99,
            'description': 'RGB keyboard',
            'image': 'cherry_mx.jpg'
        })

        with client.session_transaction() as sess:
            sess['_user_id'] = '1'  # Simulate a logged-in user

        with patch('flask_login.utils._get_user') as mock_get_user:
            # Mock the current_user as authenticated
            mock_user = MagicMock()
            mock_user.is_authenticated = True
            mock_get_user.return_value = mock_user

            response = client.get('/add_to_cart/1', follow_redirects=True)

            assert response.status_code == 200
            assert b'added to your cart' in response.data.lower()
            with client.session_transaction() as sess:
                assert '1' in sess['cart']
                assert sess['cart']['1'] == 1

    def test_add_to_cart_unauthenticated(self, client):
        """Checks that an unauthenticated user is redirected to login when adding to cart."""
        with patch('flask_login.utils._get_user') as mock_get_user:
            # Mock the current_user as not authenticated
            mock_user = MagicMock()
            mock_user.is_authenticated = False
            mock_get_user.return_value = mock_user

            response = client.get('/add_to_cart/1', follow_redirects=True)

            assert response.status_code == 200
            assert b'must be logged in' in response.data.lower()
            assert b'login' in response.data.lower()
            with client.session_transaction() as sess:
                assert 'cart' not in sess or '1' not in sess['cart']

    def test_add_custom_build(self, client):
        """Verifies that adding a custom build to the cart works."""
        with client.session_transaction() as sess:
            sess['_user_id'] = '1'  # Simulate a logged-in user

        with patch('flask_login.utils._get_user') as mock_get_user:
            # Mock the current_user as authenticated
            mock_user = MagicMock()
            mock_user.is_authenticated = True
            mock_get_user.return_value = mock_user

            response = client.get('/add_custom_build', follow_redirects=True)

            assert response.status_code == 200
            assert b'custom keyboard build added to cart' in response.data.lower()
            with client.session_transaction() as sess:
                assert 'custom_build' in sess['cart']
                assert sess['cart']['custom_build'] == 1

    def test_remove_from_cart(self, client):
        """Ensures that a product can be removed from the cart."""
        # Set up a cart with a product
        with client.session_transaction() as sess:
            sess['cart'] = {'1': 1, '2': 3}

        response = client.get('/remove_from_cart/1', follow_redirects=True)

        assert response.status_code == 200
        assert b'item removed from cart' in response.data.lower()
        with client.session_transaction() as sess:
            assert '1' not in sess['cart']
            assert '2' in sess['cart']  # Ensure other items remain

    def test_cart_view(self, client, mock_db_connection):
        """Verifies that the cart page displays the items in the cart."""
        conn, cursor = mock_db_connection

        # Simulate fetching product details based on IDs in the cart
        def side_effect_func(product_id):
            products = {
                1: type('Product', (), {'id': 1, 'name': 'Cherry MX Pro', 'price': 129.99, 'description': 'RGB keyboard', 'image': 'cherry_mx.jpg'}),
                2: type('Product', (), {'id': 2, 'name': 'Silent TypeMaster', 'price': 89.99, 'description': 'Quiet keyboard', 'image': 'silent.jpg'})
            }
            cursor.fetchone.return_value = products.get(product_id)
            return {'id': product_id, 'name': products[product_id].name, 'price': products[product_id].price,
                    'description': products[product_id].description, 'image': products[product_id].image}

        # Set up a cart with products and a custom build
        with client.session_transaction() as sess:
            sess['cart'] = {'1': 2, '2': 1, 'custom_build': 1}

        with patch('app.get_product_by_id', side_effect=side_effect_func):
            response = client.get('/cart')

            assert response.status_code == 200
            assert b'cherry mx pro' in response.data.lower()
            assert b'silent typemaster' in response.data.lower()
            assert b'custom keyboard build' in response.data.lower()
            # Won't check exact total due to potential floating-point inaccuracies
            response_data = response.get_data(as_text=True).lower()
            assert "total" in response_data

    def test_checkout(self, client):
        """Ensures that the checkout process clears the shopping cart."""
        # Set up a cart with products
        with client.session_transaction() as sess:
            sess['cart'] = {'1': 2, '2': 1}

        response = client.get('/checkout')

        assert response.status_code == 200
        assert b'checkout' in response.data.lower()
        with client.session_transaction() as sess:
            assert 'cart' not in sess # Verify the cart is cleared


class TestBuilderEndpoints:
    """Tests for keyboard builder related endpoints."""

    def test_builder_view(self, client):
        """Checks if the keyboard builder page loads."""
        response = client.get('/builder')

        assert response.status_code == 200
        assert b'builder' in response.data.lower()

    def test_builder_preview(self, client):
        """Verifies that the builder preview displays selected components."""
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
        """Ensures the builder preview handles empty selections without errors."""
        response = client.post('/builder_preview', data={
            'switches': '',
            'layout': '',
            'case': ''
        })

        assert response.status_code == 200
        assert b'preview' in response.data.lower() # It should still load the preview page


class TestGeneralPages:
    """Tests for home and test pages."""

    def test_home_page(self, client):
        """Verifies that the home page loads."""
        response = client.get('/')

        assert response.status_code == 200
        assert b'home' in response.data.lower()

    def test_home_page_authenticated(self, client):
        """Checks the home page content for an authenticated user."""
        with client.session_transaction() as sess:
            sess['_user_id'] = '1'

        with patch('flask_login.utils._get_user') as mock_get_user:
            # Mock the current_user as authenticated
            mock_user = MagicMock()
            mock_user.is_authenticated = True
            mock_user.username = 'testuser'
            mock_get_user.return_value = mock_user

            response = client.get('/')

            assert response.status_code == 200
            assert b'welcome, testuser' in response.data.lower() or b'logged in as testuser' in response.data.lower() # Check for user-specific greeting

    def test_test_page(self, client):
        """Ensures the test page loads."""