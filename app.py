from flask import Flask, render_template
import requests

app = Flask(__name__)

# URL API Sumber Data
API_URL = "https://fakestoreapi.com/products"

@app.route('/')
def index():
    # Ambil data semua produk
    response = requests.get(API_URL)
    products = response.json() # Ubah data json API jadi List Py
    return render_template('index.html', products=products) # untuk Kirim data ke file index

@app.route('/product/<int:id>')
def detail(id):
    # Ambil data satu produk spesifik berdasarkan ID
    response = requests.get(f"{API_URL}/{id}")
    product = response.json()
    return render_template('detail.html', product=product)

if __name__ == '__main__':
    app.run(debug=True)