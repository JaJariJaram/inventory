import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)
DB_NAME = 'inventory.db'

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
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

@app.route('/', methods=['GET'])
def index():
    search = request.args.get('search', '')
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        if search:
            query = f"%{search.lower()}%"
            c.execute("""
                SELECT number, MIN(name), MIN(color), SUM(quantity)
                FROM products
                WHERE LOWER(number) LIKE ? OR LOWER(name) LIKE ? OR LOWER(color) LIKE ?
                GROUP BY number
            """, (query, query, query))
        else:
            c.execute("""
                SELECT number, MIN(name), MIN(color), SUM(quantity)
                FROM products
                GROUP BY number
            """)
        groups = c.fetchall()
    return render_template('index.html', groups=groups, search=search)

@app.route('/group/<number>', methods=['GET'])
def group_detail(number):
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM products WHERE number = ?", (number,))
        products = c.fetchall()
    return render_template('group_detail.html', products=products, number=number)

@app.route('/add', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        number = request.form['number']
        name = request.form['name']
        color = request.form['color']
        quantity = request.form['quantity']
        image_url = request.form.get('image_url', '')
        if not (number and name and color and quantity.isdigit()):
            return "Niepoprawne dane", 400
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("INSERT INTO products (number, name, color, quantity, image_url) VALUES (?, ?, ?, ?, ?)",
                      (number, name, color, int(quantity), image_url))
            conn.commit()
        return redirect(url_for('index'))
    return render_template('add_product.html')

@app.route('/edit/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        if request.method == 'POST':
            number = request.form['number']
            name = request.form['name']
            color = request.form['color']
            quantity = request.form['quantity']
            image_url = request.form.get('image_url', '')
            if not (number and name and color and quantity.isdigit()):
                return "Niepoprawne dane", 400
            c.execute('''
                UPDATE products
                SET number = ?, name = ?, color = ?, quantity = ?, image_url = ?
                WHERE id = ?
            ''', (number, name, color, int(quantity), image_url, product_id))
            conn.commit()
            return redirect(url_for('group_detail', number=number))
        c.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        product = c.fetchone()
        if not product:
            return "Produkt nie istnieje", 404
    return render_template('edit_product.html', product=product)

@app.route('/delete/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("SELECT number FROM products WHERE id = ?", (product_id,))
        row = c.fetchone()
        if not row:
            return "Produkt nie istnieje", 404
        number = row[0]
        c.execute("DELETE FROM products WHERE id = ?", (product_id,))
        conn.commit()
    return redirect(url_for('group_detail', number=number))

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
