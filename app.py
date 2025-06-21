from flask import Flask, render_template, request, redirect
import sqlite3

app = Flask(__name__)
DB_NAME = 'products.db'

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                number TEXT NOT NULL,
                name TEXT NOT NULL,
                color TEXT NOT NULL,
                quantity INTEGER NOT NULL
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
                SELECT * FROM products
                WHERE LOWER(number) LIKE ? OR LOWER(name) LIKE ? OR LOWER(color) LIKE ?
            """, (query, query, query))
        else:
            c.execute("SELECT * FROM products")
        products = c.fetchall()

    return render_template('index.html', products=products, search=search)

@app.route('/add', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        number = request.form['number']
        name = request.form['name']
        color = request.form['color']
        quantity = request.form['quantity']

        if not (number and name and color and quantity.isdigit()):
            return "Niepoprawne dane", 400

        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("INSERT INTO products (number, name, color, quantity) VALUES (?, ?, ?, ?)",
                      (number, name, color, int(quantity)))
            conn.commit()
        return redirect('/')
    return render_template('add_product.html')

# ✅ NOWA TRASA – USUWANIE PRODUKTU
@app.route('/delete/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("DELETE FROM products WHERE id = ?", (product_id,))
        conn.commit()
    return redirect('/')
@app.route('/edit/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        if request.method == 'POST':
            number = request.form['number']
            name = request.form['name']
            color = request.form['color']
            quantity = request.form['quantity']

            if not (number and name and color and quantity.isdigit()):
                return "Niepoprawne dane", 400

            c.execute('''
                UPDATE products
                SET number = ?, name = ?, color = ?, quantity = ?
                WHERE id = ?
            ''', (number, name, color, int(quantity), product_id))
            conn.commit()
            return redirect('/')

        # GET - pobierz dane produktu
        c.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        product = c.fetchone()
        if not product:
            return "Produkt nie istnieje", 404
    return render_template('edit_product.html', product=product)

import os

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
