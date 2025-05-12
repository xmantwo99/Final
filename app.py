from flask import Flask, render_template, redirect, url_for, request, flash, session, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import pyodbc
from auth import auth_bp
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import dotenv

app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey'

login_manager = LoginManager(app)
login_manager.login_view = 'login'

app.register_blueprint(auth_bp)

# ---------------------------
# Database connection setup
# ---------------------------
def get_connection():
    return pyodbc.connect(
        "Driver={ODBC Driver 18 for SQL Server};"
        "Server=tcp:keyboarddb.database.windows.net,1433;"
        "Database=keyboarddb;"
        "Uid=CloudSAd21ee598;"
        "Pwd=Tellron1632;"
        "Encrypt=yes;"
        "TrustServerCertificate=yes;"
        "Connection Timeout=30;"
    )


# ---------------------------
# User model and utilities
# ---------------------------
class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

def get_user_by_id(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username FROM Users WHERE id = ?", user_id)
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if row:
        return User(row.id, row.username)
    return None

def get_user_by_username(username):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, password_hash FROM Users WHERE username = ?", username)
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if row:
        return {'id': row.id, 'username': row.username, 'password_hash': row.password_hash}
    return None

def create_user(username, password_hash):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Users (username, password_hash) VALUES (?, ?)", username, password_hash)
    conn.commit()
    cursor.close()
    conn.close()

# ---------------------------
# Product utilities
# ---------------------------
def get_all_products():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, price, description, image FROM Products")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [{'id': r.id, 'name': r.name, 'price': r.price, 'description': r.description, 'image': r.image} for r in rows]

def get_product_by_id(product_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, price, description, image FROM Products WHERE id = ?", product_id)
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if row:
        return {'id': row.id, 'name': row.name, 'price': row.price, 'description': row.description, 'image': row.image}
    return None

def add_sample_products():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Check if the Products table exists, create it if not
   
    cursor.execute("""
        IF NOT EXISTS (
            SELECT * FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = 'Products'
        )
        BEGIN
            CREATE TABLE Products (
                id INT IDENTITY(1,1) PRIMARY KEY,
                name NVARCHAR(100) NOT NULL UNIQUE,
                price FLOAT NOT NULL,
                description NVARCHAR(300),
                image NVARCHAR(300)
            )
        END
    """)

    
    sample_items = [
        ("Cherry MX Pro", 129.99, "RGB mechanical keyboard.", "cherry_mx.jpg"),
        ("Silent TypeMaster", 89.99, "Quiet mechanical keyboard.", "silent_typemaster.jpg"),
        ("Gaming Blast X", 149.99, "Gaming keyboard with macros.", "gaming_blast.jpg"),
        ("Minimalist 60%", 99.99, "Compact wireless 60% keyboard.", "minimalist.jpg"),
        ("ErgoBoard Split", 159.99, "Ergonomic split keyboard.", "ergoboard.jpg")
    ]
    
    try:
        for item in sample_items:
            # Check if the product already exists in the table by name
            cursor.execute("SELECT 1 FROM Products WHERE name = ?", (item[0],))
            result = cursor.fetchone()
            
            if result is None:
                # Insert the product if it doesn't exist
                cursor.execute("INSERT INTO Products (name, price, description, image) VALUES (?, ?, ?, ?)", item)
                print(f"Added product: {item[0]}")
            else:
                print(f"Product '{item[0]}' already exists.")
        
        conn.commit()
    except Exception as e:
        print(f"Error occurred: {e}")
    finally:
        cursor.close()
        conn.close()


# ---------------------------
# Flask-Login integration
# ---------------------------
@login_manager.user_loader
def load_user(user_id):
    return get_user_by_id(user_id)

# ---------------------------
# Routes
# ---------------------------
@app.route('/')
def home():
    return render_template('home.html', user=current_user)

@app.route('/me')
def me():
    return session.get('user', {})

@app.route('/test')
def test():
    return render_template('test.html', user=current_user)

@app.route('/products')
def products():
    product_list = get_all_products()
    return render_template('products.html', user=current_user, products=product_list)

@app.route('/add_to_cart/<int:product_id>')
def add_to_cart(product_id):
    if not current_user.is_authenticated:
        flash("You must be logged in to add items to the cart.", "danger")
        return redirect(url_for('login'))
    product = get_product_by_id(product_id)
    cart = session.get('cart', {})
    cart[str(product_id)] = cart.get(str(product_id), 0) + 1
    session['cart'] = cart
    flash(f"{product['name']} added to your cart!", "success")
    return redirect(url_for('products'))

@app.route('/add_custom_build')
def add_custom_build():
    if not current_user.is_authenticated:
        flash("Please log in to add a custom build.", "danger")
        return redirect(url_for('login'))
    cart = session.get('cart', {})
    cart['custom_build'] = cart.get('custom_build', 0) + 1
    session['cart'] = cart
    flash("Custom keyboard build added to cart!", "success")
    return redirect(url_for('home'))

@app.route('/remove_from_cart/<product_id>')
def remove_from_cart(product_id):
    cart = session.get('cart', {})
    if product_id in cart:
        del cart[product_id]
    session['cart'] = cart
    flash("Item removed from cart.", "info")
    return redirect(url_for('cart'))

@app.route('/cart')
def cart():
    cart = session.get('cart', {})
    items = []
    total = 0
    for product_id, quantity in cart.items():
        if product_id == 'custom_build':
            item = {'product': {'name': "Custom Keyboard Build", 'price': 175.00}, 'quantity': quantity, 'total': 175.00 * quantity}
        else:
            product = get_product_by_id(int(product_id))
            item = {'product': product, 'quantity': quantity, 'total': product['price'] * quantity}
        items.append(item)
        total += item['total']
    return render_template('cart.html', user=current_user, items=items, total=total)

@app.route('/checkout')
def checkout():
    session.pop('cart', None)
    return render_template('checkout.html', user=current_user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user_data = get_user_by_username(username)
        if user_data and check_password_hash(user_data['password_hash'], password):
            login_user(User(user_data['id'], user_data['username']))
            return redirect(url_for('home'))
        flash('Invalid username or password.', 'danger')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if get_user_by_username(username):
            flash('Username already exists.', 'danger')
        else:
            hashed_pw = generate_password_hash(password)
            create_user(username, hashed_pw)
            flash('Account created! You can now log in.', 'success')
            return redirect(url_for('login'))
    return render_template('signup.html')


@app.route('/google-signin', methods=['POST'])
def google_signin():
    try:
        token = request.json.get('token')
        idinfo = id_token.verify_oauth2_token(token, google_requests.Request(), "288200736270-vc4er89mo72r3lhc79ai908if78jh896.apps.googleusercontent.com")

        # Extract user info
        email = idinfo['email']
        name = idinfo.get('name', '')

        # Check if user exists or create new one
        user = get_user_by_username(email)
        if not user:
            create_user(email, "")  # Optionally generate a random password or leave blank

        # Log the user in (use your session/login logic here)
        session['user'] = email
        return jsonify({"success": True})
    except Exception as e:
        print("Google Sign-In error:", e)
        return jsonify({"success": False, "error": str(e)})

@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.pop('cart', None)
    return redirect(url_for('home'))

@app.route('/builder')
def builder():
    return render_template('builder.html')

@app.route('/builder_preview', methods=['POST'])
def builder_preview():
    switches = request.form.get('switches')
    layout = request.form.get('layout')
    case = request.form.get('case')
    return render_template('builder_preview.html', switches=switches, layout=layout, case=case)

@app.route('/add-sample-products')
def add_sample_products_route():
    add_sample_products()
    return "Sample products added!"

if __name__ == '__main__':
    app.run(debug=True)
