from flask_login import UserMixin
import pyodbc

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
