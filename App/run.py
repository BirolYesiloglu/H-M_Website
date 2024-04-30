from itertools import product
import sqlite3 as sql
from flask import Flask, jsonify, render_template, request, url_for

app = Flask(__name__)

# Initialize the database with appropriate schema for H&M products
def initDB():
    conn = sql.connect('hm_database.db')
    print("Opened database successfully")
    
    # Adjust table schema to suit H&M product attributes
    conn.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        price REAL NOT NULL,
        category TEXT NOT NULL,
        subcategory TEXT NOT NULL,
        image_filename TEXT NOT NULL
    )''')
    print("Table created successfully")
    conn.close()

# Function to extract unique subcategories for a given category
def get_unique_subcategories(rows, category):
    displayed_subcategories = set()
    unique_subcategories = []
    for row in rows:
        if row['category'] == category and row['subcategory'] not in displayed_subcategories:
            displayed_subcategories.add(row['subcategory'])
            unique_subcategories.append(row['subcategory'])
    return unique_subcategories

@app.route('/')
def home():
    con = sql.connect('hm_database.db')
    con.row_factory = sql.Row
    cur = con.cursor()
    
    cur.execute("SELECT * FROM products")
    products = cur.fetchall()

    # Determine the number of products per slide
    products_per_slide = 4
    slides = [products[i:i + products_per_slide] for i in range(0, len(products), products_per_slide)]

    unique_categories = set(product['category'] for product in products)

    subcategories_counters = {}
    for product in products:
        category = product['category']
        subcategory = product['subcategory']
        if category not in subcategories_counters:
            subcategories_counters[category] = {}
        if subcategory not in subcategories_counters[category]:
            subcategories_counters[category][subcategory] = 1
        else:
            subcategories_counters[category][subcategory] += 1

    con.close()

    return render_template(
        'index.html',
        slides=slides,
        unique_categories=unique_categories,
        subcategories_counters=subcategories_counters,
        get_unique_subcategories=get_unique_subcategories
    )

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    con = sql.connect('hm_database.db')
    con.row_factory = sql.Row
    cur = con.cursor()
    cur.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    product = cur.fetchone()

    if product:
        product = dict(product)
        if 'sizes' in product and product['sizes']:
            sizes = product['sizes'].split(',')  # Convert the sizes string to a list
            product['sizes'] = [{'name': size, 'available': True} for size in sizes]

    return render_template('detail.html', product=product)


@app.route('/search', methods=['GET', 'POST'])
def search():
    search_key = request.values.get('searchKey', '')  # supports both GET and POST
    sort_by = request.values.get('sort_by', 'price_asc')  # default sort by price ascending
    size_filter = request.values.get('size_filter', '')  # default no size filter
    
    # Connect to the database
    con = sql.connect('hm_database.db')
    con.row_factory = sql.Row
    cur = con.cursor()

    # Build SQL query based on sorting and filtering parameters
    query = "SELECT * FROM products WHERE name LIKE ?"
    params = ('%' + search_key + '%',)

    if sort_by == 'price_asc':
        query += " ORDER BY price ASC"
    elif sort_by == 'price_desc':
        query += " ORDER BY price DESC"

    # Execute search query with size filter
    if size_filter:
        cur.execute("SELECT * FROM products WHERE name LIKE ? AND size = ?", ('%' + search_key + '%', size_filter))
    else:
        cur.execute("SELECT * FROM products WHERE name LIKE ?", ('%' + search_key + '%',))
    rows = cur.fetchall()


    cur.execute(query, params)
    rows = cur.fetchall()
    
    # Filter by size if specified
    if size_filter:
        rows = [row for row in rows if size_filter in row['sizes']]

    unique_categories = set(row['category'] for row in rows)

    subcategories_counters = {}
    for row in rows:
        category = row['category']
        subcategory = row['subcategory']
        if category not in subcategories_counters:
            subcategories_counters[category] = {}
        if subcategory not in subcategories_counters[category]:
            subcategories_counters[category][subcategory] = 1
        else:
            subcategories_counters[category][subcategory] += 1

    return render_template('search_result.html',rows=rows,
        unique_categories=unique_categories,
        subcategories_counters=subcategories_counters,
        get_unique_subcategories=get_unique_subcategories,
        search_key=search_key,
        sort_by=sort_by,
        size_filter=size_filter
    )


@app.route('/category/<string:categoryKey>')
def searchCategory(categoryKey):
    con = sql.connect('hm_database.db')
    con.row_factory = sql.Row
    cur = con.cursor()
    
    cur.execute("SELECT * FROM products WHERE subcategory LIKE ? OR category LIKE ?", ('%' + categoryKey + '%', '%' + categoryKey + '%',))
    rows = cur.fetchall()
    
    return render_template(
        'search_result.html',
        rows=rows,
        search_key=categoryKey,
        category=categoryKey  # Pass categoryKey to the template
    )

@app.route('/filter-category')
def filter_category():
    category_name = request.args.get('category', None)
    if not category_name:
        return jsonify(error='Category not provided'), 400

    # Connect to database and fetch products for the specified category
    con = sql.connect('hm_database.db')
    con.row_factory = sql.Row
    cur = con.cursor()
    cur.execute("SELECT * FROM products WHERE LOWER(category) = LOWER(?)", (category_name,))
    rows = cur.fetchall()

    # Convert rows to a list of dictionaries
    products = [dict(row) for row in rows]

    return jsonify(products)

@app.route('/handle_search', methods=['GET', 'POST'])
def handle_search():
    search_key = request.values.get('search_key', '')  # supports both GET and POST
    sort_by = request.values.get('sort_by', 'price_asc')  # default sort by price ascending
    size_filter = request.values.get('size_filter', '')  # default no size filter
    
    # Connect to the database
    con = sql.connect('hm_database.db')
    con.row_factory = sql.Row
    cur = con.cursor()

    # Build SQL query based on sorting and filtering parameters
    query = "SELECT * FROM products WHERE name LIKE ?"
    params = ['%' + search_key + '%']

    if size_filter:
        query += " AND sizes LIKE ?"
        params.append('%' + size_filter + '%')

    if sort_by == 'price_asc':
        query += " ORDER BY price ASC"
    elif sort_by == 'price_desc':
        query += " ORDER BY price DESC"

    # Execute search query
    cur.execute(query, params)
    rows = cur.fetchall()

    return render_template('search_result.html', rows=rows)


if __name__ == '__main__':
    initDB()
    app.run(debug=True)