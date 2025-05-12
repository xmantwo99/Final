from flask import Blueprint, request, jsonify, session
from google.oauth2 import id_token
from google.auth.transport import requests as grequests
from flask_login import login_user
from app import get_user_by_username, create_user, User  

auth_bp = Blueprint('auth', __name__)

# ✅ Correct Google Client ID
GOOGLE_CLIENT_ID = "288200736270-vc4er89mo72r3lhc79ai908if78jh896.apps.googleusercontent.com"

@auth_bp.route('/login-with-google', methods=['POST'])
def login_with_google():
    try:
        token = request.json.get('id_token')
        idinfo = id_token.verify_oauth2_token(token, grequests.Request(), GOOGLE_CLIENT_ID)

        session['user'] = {
            'email': idinfo['email'],
            'name': idinfo.get('name', '')
        }

        return jsonify({
            'message': f"Welcome {idinfo.get('name', '')}",
            'success': True,
            'redirect': '/'
        }), 200
    except ValueError as ve:
        return jsonify({'error': 'Invalid token', 'success': False, 'message': str(ve)}), 400
    except Exception as e:
        return jsonify({'error': 'Unexpected error', 'success': False, 'message': str(e)}), 500

@auth_bp.route('/google-signin', methods=['POST'])
def google_signin():
    try:
        token = request.json.get('token')
        idinfo = id_token.verify_oauth2_token(token, grequests.Request(), GOOGLE_CLIENT_ID)

        email = idinfo['email']
        name = idinfo.get('name', '')

        user_data = get_user_by_username(email)
        if not user_data:
            create_user(email, "")  # ✅ Create new user with blank password

        user_data = get_user_by_username(email)  # ✅ Re-fetch to get ID
        user_obj = User(user_data['id'], user_data['username'])  # ✅ Wrap in User model
        login_user(user_obj)  # ✅ Actually log the user in

        session['user'] = {'email': email, 'name': name}  # Optional: still storing in session

        return jsonify({
            'success': True,
            'message': f"Welcome {name}",
            'redirect': '/'
        }), 200
    except Exception as e:
        print("Google sign-in error:", e)
        return jsonify({'success': False, 'message': str(e)}), 400

@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.pop('user', None)
    return jsonify({'message': 'Logged out', 'success': True}), 200
