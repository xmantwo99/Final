from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Models
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(300))
    image = db.Column(db.String(300))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def home():
    return render_template('home.html', user=current_user)

@app.route('/products')
def products():
    products = Product.query.all()
    return render_template('products.html', user=current_user, products=products)

@app.route('/add_to_cart/<int:product_id>')
def add_to_cart(product_id):
    if not current_user.is_authenticated:
        flash("You must be logged in to add items to the cart.", "danger")
        return redirect(url_for('login'))
    product = Product.query.get_or_404(product_id)
    cart = session.get('cart', {})
    cart[str(product_id)] = cart.get(str(product_id), 0) + 1
    session['cart'] = cart
    flash(f"{product.name} added to your cart!", "success")
    return redirect(url_for('products'))

@app.route('/add_custom_build')
def add_custom_build():
    if not current_user.is_authenticated:
        flash("Please log in to add a custom build.", "danger")
        return redirect(url_for('login'))
    cart = session.get('cart', {})
    custom_key = 'custom_build'
    cart[custom_key] = cart.get(custom_key, 0) + 1
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
            name = "Custom Keyboard Build"
            price = 175.00
            item_total = price * quantity
            total += item_total
            items.append({'product': {'name': name, 'price': price}, 'quantity': quantity, 'total': item_total})
        else:
            product = Product.query.get(int(product_id))
            if product:
                item_total = product.price * quantity
                total += item_total
                items.append({'product': product, 'quantity': quantity, 'total': item_total})
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
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('home'))
        flash('Invalid username or password.', 'danger')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'danger')
        else:
            hashed_pw = generate_password_hash(password)
            new_user = User(username=username, password_hash=hashed_pw)
            db.session.add(new_user)
            db.session.commit()
            flash('Account created! You can now log in.', 'success')
            return redirect(url_for('login'))
    return render_template('signup.html')

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
def add_sample_products():
    sample_items = [
        Product(name="Cherry MX Pro", price=129.99, description="RGB mechanical keyboard.", image="cherry_mx.jpg"),
        Product(name="Silent TypeMaster", price=89.99, description="Quiet mechanical keyboard for office use.", image="silent_typemaster.jpg"),
        Product(name="Gaming Blast X", price=149.99, description="High-performance gaming keyboard with macros.", image="gaming_blast.jpg"),
        Product(name="Minimalist 60%", price=99.99, description="Compact wireless 60% keyboard.", image="minimalist.jpg"),
        Product(name="ErgoBoard Split", price=159.99, description="Ergonomic split layout mechanical keyboard.", image="ergoboard.jpg"),
    ]
    db.session.bulk_save_objects(sample_items)
    db.session.commit()
    return "Sample products added!"

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
