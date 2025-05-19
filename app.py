from flask import Flask, render_template, request, redirect, url_for, session, send_file
from werkzeug.security import generate_password_hash, check_password_hash
import os
import sqlite3
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your_secret_key'

DB_PATH = 'users.db'
UPLOAD_FOLDER = 'uploads'
CONVERTED_FOLDER = 'converted'
LOG_FILE = 'logs/ingresos.txt'

@app.before_first_request
def create_tables():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                 id INTEGER PRIMARY KEY,
                 username TEXT UNIQUE NOT NULL,
                 password TEXT NOT NULL)''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    if 'user' in session:
        return render_template('dashboard.html', user=session['user'])
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
        except sqlite3.IntegrityError:
            return "Usuario ya existe"
        conn.close()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT password FROM users WHERE username = ?", (username,))
        row = c.fetchone()
        conn.close()
        if row and check_password_hash(row[0], password):
            session['user'] = username
            with open(LOG_FILE, 'a') as f:
                f.write("User: {} - Login at {}
".format(username, datetime.now()))
            return redirect(url_for('index'))
        return "Credenciales incorrectas"
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

@app.route('/convert', methods=['POST'])
def convert_file():
    if 'file' not in request.files:
        return 'No file part'
    file = request.files['file']
    if file.filename == '':
        return 'No selected file'
    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)
    converted_path = os.path.join(CONVERTED_FOLDER, f"{filename}.converted.txt")
    with open(filepath, 'rb') as fin, open(converted_path, 'wb') as fout:
        fout.write(fin.read())  # Simula conversión
    return send_file(converted_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
