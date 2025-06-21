full_app_py = '''
import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, g

app = Flask(__name__)
app.secret_key = 'tajny_klucz'
DB_NAME = 'inventory.db'

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                role TEXT NOT NULL
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                number TEXT NOT NULL,
                name TEXT NOT NULL,
                color TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                image_url TEXT
            )
        ''')
        conn.commit()
        # Dodaj użytkowników testowych jeśli nie istnieją
        c.execute("SELECT COUNT(*) FROM users")
        if c.fetchone()[0] == 0:
            c.execute("INSERT INTO users (username, password, role) VALUES ('admin', 'admin', 'admin')")
            c.execute("INSERT INTO users (username, password, role) VALUES ('user', 'user', 'user')")
            conn.commit()

@app.before_request
def before_request():
    g.user = session.get('user')

def login_required(f):
    def decorated(*args, **kwargs):
        if not g.user:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated.__name__ = f.__name__
    return decorated

def admin_required(f):
    def decorated(*args, **kwargs):
        if not g.user or g.user['role'] != 'admin':
            return "Dostęp tylko dla administratora", 403
        return f(*args, **kwargs)
    decorated.__name__ = f.__name__
    return decorated

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
            user = c.fetchone()
            if user:
                session['user'] = {'username': user[1], 'role': user[3]}
                return redirect(url_for('index'))
            else:
                error = "Nieprawidłowe dane logowania"
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    search = request.args.get('search', '')
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        if search:
            q = f"%{search.lower()}%"
            c.execute("""
                SELECT number, MIN(name), MIN(color), SUM(quantity)
                FROM products
                WHERE LOWER(number) LIKE ? OR LOWER(name) LIKE ? OR LOWER(color) LIKE ?
                GROUP BY number
            """, (q, q, q))
        else:
            c.execute("""
                SELECT number, MIN(name), MIN(color), SUM(quantity)
                FROM products
                GROUP BY number
            """)
        groups = c.fetchall()
    return render_template('index.html', groups=groups, search=search)

@app.route('/admin')
@admin_required
def admin():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(DISTINCT number) FROM products")
        group_count = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM products")
        product_count = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM products WHERE quantity < 5")
        low_stock = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM products WHERE image_url IS NULL OR image_url = ''")
        no_image = c.fetchone()[0]
        c.execute("SELECT * FROM products ORDER BY id DESC")
        products = c.fetchall()
    return render_template('admin.html', products=products, group_count=group_count, product_count=product_count, low_stock=low_stock, no_image=no_image)

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
'''
