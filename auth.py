from flask import Blueprint, request, jsonify, session
from google.oauth2 import id_token
from google.auth.transport import requests as grequests

auth_bp = Blueprint('auth', __name__)
GOOGLE_CLIENT_ID = "288200736270-vc4er89mo72r3lhc79ai908if78jh896.apps.googleusercontent.com"

@auth_bp.route('/login-with-google', methods=['POST'])
def login_with_google():
    try:
        token = request.json.get('id_token')
        idinfo = id_token.verify_oauth2_token(token, grequests.Request(), GOOGLE_CLIENT_ID)

        user_email = idinfo['email']
        user_name = idinfo.get('name', '')
        session['user'] = {
            'email': user_email,
            'name': user_name
        }

        return jsonify({'message': f'Welcome {user_name}'}), 200
    except ValueError:
        return jsonify({'error': 'Invalid token'}), 400

@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.pop('user', None)
    return jsonify({'message': 'Logged out'}), 200
