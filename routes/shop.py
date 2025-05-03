from flask import Blueprint, render_template
from models import Product

shop = Blueprint('shop', __name__)

@shop.route('/')
def home():
    return render_template('home.html')

@shop.route('/shop')
def show_products():
    products = Product.query.all()
    return render_template('shop.html', products=products)

@shop.route('/checkout')
def checkout():
    return render_template('checkout.html')
