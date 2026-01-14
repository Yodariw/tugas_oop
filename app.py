from flask import Flask, render_template, request, session, redirect, url_for, flash
import requests
import random
import math

app = Flask(__name__)
app.secret_key = 'rahasia_kelompok_kita_aman_jaya' 
API_URL = "https://fakestoreapi.com/products"

# ================= KONFIGURASI RUPIAH =================
KURS_USD_IDR = 15500 

def format_rupiah(value):
    """
    Mengubah harga USD ke Rupiah dengan format 'Rp X.XXX.XXX'
    """
    try:
        # Konversi ke IDR
        idr_value = float(value) * KURS_USD_IDR
        # Format ribuan dengan titik (indonesia style)
        return "Rp {:,.0f}".format(idr_value).replace(",", ".")
    except (ValueError, TypeError):
        return "Rp 0"

# Daftarkan filter ini ke Jinja2 agar bisa dipakai di HTML
app.jinja_env.filters['rupiah'] = format_rupiah
# ======================================================

# --- FUNGSI BANTUAN ---
def get_products():
    try:
        response = requests.get(API_URL)
        return response.json()
    except:
        return []

# --- CONTEXT PROCESSOR (NAVBAR COUNT & AUTO FIX ERROR) ---
@app.context_processor
def inject_counts():
    cart = session.get('cart', {})
    
    # [PENGAMAN] Jika data lama (List) masih nyangkut, reset jadi Dictionary
    if isinstance(cart, list): 
        cart = {}
        session['cart'] = {}
        session.modified = True
    
    # Hitung total barang (Sum of values)
    total_qty = sum(cart.values())
    
    wishlist = session.get('wishlist', [])
    return dict(cart_count=total_qty, wishlist_count=len(wishlist))

# --- ROUTES UTAMA ---
@app.route('/')
def index():
    search_query = request.args.get('q', '').lower()
    sort_option = request.args.get('sort', 'default')
    page = request.args.get('page', 1, type=int)
    per_page = 8

    products = get_products()

    # Filter Search
    if search_query:
        products = [p for p in products if search_query in p['title'].lower() or search_query in p['category'].lower()]

    # Filter Sort
    if sort_option == 'price_asc':
        products = sorted(products, key=lambda x: x['price'])
    elif sort_option == 'price_desc':
        products = sorted(products, key=lambda x: x['price'], reverse=True)

    # Pagination
    total_products = len(products)
    total_pages = math.ceil(total_products / per_page)
    start = (page - 1) * per_page
    end = start + per_page
    paginated_products = products[start:end]

    wishlist = session.get('wishlist', [])

    return render_template('index.html', 
    products=paginated_products, 
    page=page, 
    total_pages=total_pages,
    sort_option=sort_option, 
    search_query=search_query,
    active_category='all',
    wishlist=wishlist)

@app.route('/category/<string:name>')
def category(name):
    all_products = get_products()
    products = [p for p in all_products if p['category'] == name]
    wishlist = session.get('wishlist', [])
    return render_template('index.html', products=products, page=1, total_pages=1, active_category=name, wishlist=wishlist)

@app.route('/product/<int:id>')
def detail(id):
    try:
        response = requests.get(f"{API_URL}/{id}")
        product = response.json()
        all_products = get_products()
        related = [p for p in all_products if p['category'] == product['category'] and p['id'] != id]
        random.shuffle(related)
        wishlist = session.get('wishlist', [])
        return render_template('detail.html', product=product, related=related[:4], wishlist=wishlist)
    except:
        return redirect('/')

# --- CART LOGIC ---
@app.route('/add_to_cart/<int:id>', methods=['GET', 'POST'])
def add_to_cart(id):
    cart = session.get('cart', {})
    if isinstance(cart, list): cart = {}

    qty = int(request.form.get('quantity', 1))
    str_id = str(id) 
    
    if str_id in cart:
        cart[str_id] += qty
    else:
        cart[str_id] = qty

    session['cart'] = cart
    session.modified = True
    flash(f'Berhasil menambah {qty} barang! 🛒', 'success')
    return redirect(request.referrer)

@app.route('/cart')
def cart():
    cart_dict = session.get('cart', {})
    if isinstance(cart_dict, list): cart_dict = {} 

    all_products = get_products()
    cart_items = []
    grand_total = 0
    
    for str_id, qty in cart_dict.items():
        product = next((p for p in all_products if str(p['id']) == str_id), None)
        if product:
            product['qty'] = qty
            # HITUNG SUBTOTAL DALAM USD DULU
            product['subtotal_usd'] = product['price'] * qty
            # KONVERSI KE RUPIAH UNTUK TAMPILAN
            product['price_idr'] = format_rupiah(product['price'])
            product['subtotal_idr'] = format_rupiah(product['subtotal_usd'])
            
            grand_total += product['subtotal_usd']
            cart_items.append(product)
            
    # Total akhir dalam Rupiah
    grand_total_idr = format_rupiah(grand_total)
            
    return render_template('cart.html', cart_items=cart_items, total=grand_total_idr)

@app.route('/update_cart/<int:id>', methods=['POST'])
def update_cart(id):
    cart = session.get('cart', {})
    if isinstance(cart, list): cart = {}
    
    str_id = str(id)
    new_qty = int(request.form.get('quantity', 1))
    
    if new_qty > 0:
        cart[str_id] = new_qty
    else:
        cart.pop(str_id, None)
        
    session['cart'] = cart
    session.modified = True
    return redirect('/cart')

@app.route('/remove_cart/<int:id>')
def remove_cart(id):
    cart = session.get('cart', {})
    if isinstance(cart, list): cart = {}
    
    str_id = str(id)
    if str_id in cart:
        cart.pop(str_id)
        session.modified = True
    return redirect('/cart')

@app.route('/clear_cart')
def clear_cart():
    session['cart'] = {}
    return redirect('/cart')

# --- WISHLIST LOGIC ---
@app.route('/add_to_wishlist/<int:id>')
def add_to_wishlist(id):
    if 'wishlist' not in session: session['wishlist'] = []
    if id not in session['wishlist']:
        session['wishlist'].append(id)
        session.modified = True
        flash('Disimpan ke Favorit ❤️', 'success')
    return redirect(request.referrer)

@app.route('/remove_wishlist/<int:id>')
def remove_wishlist(id):
    w_list = session.get('wishlist', [])
    if id in w_list:
        w_list.remove(id)
        session.modified = True
    return redirect(request.referrer)

@app.route('/wishlist')
def wishlist():
    wish_ids = session.get('wishlist', [])
    all_products = get_products()
    wish_items = [p for p in all_products if p['id'] in wish_ids]
    return render_template('wishlist.html', wish_items=wish_items)

if __name__ == '__main__':
    app.run(debug=True)