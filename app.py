import base64
import json
from io import BytesIO
from flask import Flask, render_template, request, redirect, jsonify
import qrcode
import re
import firebase_admin
from firebase_admin import credentials, auth, db
import pyrebase

app = Flask(__name__)

# Firebase configuration for client SDK
firebaseConfig = {
    "apiKey": "AIzaSyC5iauvSScXMmf4jowxqBbIox0PP7b4A3M",
    "authDomain": "custom-qr-code-775.firebaseapp.com",
    "databaseURL": "https://custom-qr-code-775-default-rtdb.firebaseio.com",
    "projectId": "custom-qr-code-775",
    "storageBucket": "custom-qr-code-775.appspot.com",
    "messagingSenderId": "423549283128",
    "appId": "1:423549283128:web:5acf328c31292465146fcd",
    "measurementId": "G-K3S3DR9ZN1"
}

# Initialize Firebase Admin SDK with service account key
cred = credentials.Certificate('serviceAccountKey.json')  # Path to your service account key
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://custom-qr-code-775-default-rtdb.firebaseio.com/'  # Your database URL
})

# Initialize Firebase client SDK (Pyrebase) for authentication
firebase = pyrebase.initialize_app(firebaseConfig)
auth_client = firebase.auth()
db_client = firebase.database()

# Secret key for Flask sessions (required for flash messages)
app.secret_key = 'your_secret_key'


@app.route('/')
def login():
    return render_template('login.html')


@app.route('/home')
def home():
    return render_template('index.html')


@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        c_password = request.form['re_pass']

        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return jsonify({'status': 'error', 'title': 'Invalid Email', 'message': 'Invalid email format!'}), 400

        if len(password) < 6:
            return jsonify({'status': 'error', 'title': 'Weak Password', 'message': 'Password must be at least 6 characters long.'}), 400

        if password == c_password:
            try:
                user = auth_client.create_user_with_email_and_password(email, password)
                return jsonify({'status': 'success', 'title': 'Success!', 'message': 'Registration successful! Please log in to continue.'}), 200
            except Exception as e:
                error_msg = str(e)
                if "EMAIL_EXISTS" in error_msg:
                    return jsonify({'status': 'error', 'title': 'Email Exists', 'message': 'This email is already in use. Please use another email.'}), 400
                else:
                    return jsonify({'status': 'error', 'title': 'Registration Error', 'message': f'Error during registration: {error_msg}'}), 400
        else:
            return jsonify({'status': 'error', 'title': 'Password Mismatch', 'message': "Passwords don't match!"}), 400

    return render_template('registration.html')


@app.route('/user_login', methods=['POST', 'GET'])
def user_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        if not email or '@' not in email:
            return jsonify({'status': 'error', 'title': 'Invalid Email', 'message': 'Invalid email address. Please enter a valid email.'}), 400

        try:
            user = auth_client.sign_in_with_email_and_password(email, password)
            return jsonify({'status': 'success', 'title': 'Success!', 'message': 'Login successful! Redirecting to home...'}), 200
        except Exception as e:
            error_msg = str(e)
            return jsonify({'status': 'error', 'title': 'Login Failed', 'message': f'Login failed: {error_msg}'}), 400

    return render_template('login.html')


@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        try:
            auth_client.send_password_reset_email(email)
            return jsonify({'status': 'success', 'title': 'Success!', 'message': 'Password reset email sent successfully ! Check your inbox.'}), 200
        except Exception as e:
            error_msg = str(e)
            return jsonify({'status': 'error', 'title': 'Error', 'message': f'Error: {error_msg}'}), 400
    return render_template('forgot_password.html')


@app.route("/show_qr", methods=['POST', 'GET'])
def show_qr():
    if request.method == "POST":
        try:
            name = request.form['name']
            email = request.form['email']
            custom_labels = request.form.getlist('custom_label[]')
            custom_values = request.form.getlist('custom_value[]')

            unique_key = f"user_{email.replace('.', '_').replace('@', '_at_')}"  # Global Unique ID for QR Code

            data = {
                'global_id': "MY_APP_QR_CODE",  # Added global identifier
                'id': unique_key,
                'name': name,
                'email': email,
                'custom_fields': {label: value for label, value in zip(custom_labels, custom_values)}
            }

            db.reference(f"users/{unique_key}/qr_codes").push(data)

            encrypted_data = base64.b64encode(json.dumps(data).encode()).decode()
            buffer = BytesIO()
            img = qrcode.make(encrypted_data)
            img.save(buffer)
            buffer.seek(0)
            encoded_img = base64.b64encode(buffer.getvalue())

            return render_template('showQR.html', img=encoded_img.decode('utf-8'))
        except Exception as e:
            return jsonify({'status': 'error', 'title': 'QR Code Error', 'message': f'Error generating QR code: {str(e)}'}), 400
    return redirect('/home')


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=3000)