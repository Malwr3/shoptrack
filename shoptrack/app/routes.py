from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from .models import get_db

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    db = get_db()
    # Fetch summary stats for dashboard
    today_sales = db.execute("SELECT SUM(total) as total, COUNT(*) as count FROM sales WHERE date(created_at) = date('now')").fetchone()
    low_stock = db.execute("SELECT * FROM products WHERE quantity <= reorder_level").fetchall()
    recent_sales = db.execute("SELECT s.*, u.username FROM sales s JOIN users u ON s.cashier_id = u.id ORDER BY s.created_at DESC LIMIT 5").fetchall()
    
    return render_template('dashboard.html', today_sales=today_sales, low_stock=low_stock, recent_sales=recent_sales)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        
        if user and user['password'] == password: # In production, use werkzeug.security hashes
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            flash('Logged in successfully!', 'success')
            return redirect(url_for('main.index'))
        flash('Invalid username or password.', 'danger')
    return render_template('login.html')

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.login'))

@bp.route('/products')
def products():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    db = get_db()
    search = request.args.get('search', '')
    query = "SELECT p.*, c.name as category_name FROM products p LEFT JOIN categories c ON p.category_id = c.id WHERE p.name LIKE ?"
    items = db.execute(query, (f'%{search}%',)).fetchall()
    return render_template('products.html', products=items, search=search)

@bp.route('/products/add', methods=['GET', 'POST'])
def add_product():
    if session.get('role') not in ['admin', 'manager']:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('main.index'))
    
    db = get_db()
    if request.method == 'POST':
        sku = request.form['sku']
        name = request.form['name']
        category_id = request.form['category_id']
        buying_price = float(request.form['buying_price'])
        selling_price = float(request.form['selling_price'])
        quantity = int(request.form['quantity'])
        reorder_level = int(request.form['reorder_level'])
        
        db.execute('''INSERT INTO products (sku, name, category_id, buying_price, selling_price, quantity, reorder_level)
                      VALUES (?, ?, ?, ?, ?, ?, ?)''',
                   (sku, name, category_id, buying_price, selling_price, quantity, reorder_level))
        db.commit()
        flash('Product added successfully!', 'success')
        return redirect(url_for('main.products'))
    
    categories = db.execute("SELECT * FROM categories").fetchall()
    return render_template('add_product.html', categories=categories)

@bp.route('/sales', methods=['GET', 'POST'])
def sales():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    db = get_db()
    if 'cart' not in session:
        session['cart'] = []

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            product_id = int(request.form['product_id'])
            product = db.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
            if product:
                cart = session['cart']
                found = False
                for item in cart:
                    if item['id'] == product_id:
                        item['qty'] += 1
                        found = True
                        break
                if not found:
                    cart.append({'id': product['id'], 'name': product['name'], 'price': product['selling_price'], 'qty': 1})
                session['cart'] = cart
        elif action == 'clear':
            session['cart'] = []
        elif action == 'complete':
            cart = session['cart']
            if not cart:
                flash('Cart is empty!', 'warning')
                return redirect(url_for('main.sales'))
            
            subtotal = sum(item['price'] * item['qty'] for item in cart)
            discount = float(request.form.get('discount', 0))
            total = subtotal - discount
            payment_method = request.form.get('payment_method', 'Cash')
            receipt_no = f"#{abs(hash(str(session['user_id']) + str(total))) % 10000:04d}"
            
            cursor = db.cursor()
            cursor.execute('''INSERT INTO sales (receipt_no, cashier_id, subtotal, discount, total, payment_method)
                              VALUES (?, ?, ?, ?, ?, ?)''',
                           (receipt_no, session['user_id'], subtotal, discount, total, payment_method))
            sale_id = cursor.lastrowid
            
            for item in cart:
                cursor.execute('INSERT INTO sale_items (sale_id, product_id, quantity, price) VALUES (?, ?, ?, ?)',
                               (sale_id, item['id'], item['qty'], item['price']))
                # Auto stock deduction[cite: 7]
                cursor.execute('UPDATE products SET quantity = quantity - ? WHERE id = ?', (item['qty'], item['id']))
            
            db.commit()
            session['cart'] = []
            flash(f'Sale completed! Receipt {receipt_no}', 'success')
            return redirect(url_for('main.receipt', sale_id=sale_id))

    products_list = db.execute("SELECT * FROM products").fetchall()
    return render_template('sales.html', products=products_list, cart=session.get('cart', []))

@bp.route('/receipt/<int:sale_id>')
def receipt(sale_id):
    db = get_db()
    sale = db.execute("SELECT s.*, u.username FROM sales s JOIN users u ON s.cashier_id = u.id WHERE s.id = ?", (sale_id,)).fetchone()
    items = db.execute("SELECT si.*, p.name FROM sale_items si JOIN products p ON si.product_id = p.id WHERE si.sale_id = ?", (sale_id,)).fetchall()
    return render_template('receipt.html', sale=sale, items=items)
@bp.route('/stock-in', methods=['GET', 'POST'])
def stock_in():
    if session.get('role') not in ['admin', 'manager']:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('main.index'))
    
    db = get_db()
    if request.method == 'POST':
        supplier_name = request.form['supplier']
        product_id = int(request.form['product_id'])
        qty_received = int(request.form['quantity'])
        
        cursor = db.cursor()
        cursor.execute("INSERT INTO suppliers (name) VALUES (?)", (supplier_name,))
        
        # Increase product quantity automatically on delivery confirmation[cite: 7]
        db.execute("UPDATE products SET quantity = quantity + ? WHERE id = ?", (qty_received, product_id))
        db.commit()
        
        flash('Stock received and inventory updated successfully!', 'success')
        return redirect(url_for('main.products'))
        
    products = db.execute("SELECT * FROM products").fetchall()
    return render_template('stock_in.html', products=products)
