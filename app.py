import jwt
import os
# import datetime
from datetime import datetime,timedelta,timezone,time
from flask import Flask, request, jsonify,session,render_template,redirect,url_for,flash
from werkzeug.utils import secure_filename

import sqlite3
import hashlib
import re
from queries import *
import secrets
import requests
import ollama
import sqlite3
import markdown
from utils import fetch_and_store_images
from openai import OpenAI


def get_db_connection():
    conn = sqlite3.connect('fashion_sense.sqlite3')  # Replace with your actual DB filename
    conn.row_factory = sqlite3.Row  # So we can access columns by name, like row['category_name']
    return conn
flask_secret_key = secrets.token_hex(16)  # 16 bytes = 128 bits

# Generate a secret key for JWT (256-bit length)
jwt_secret_key = secrets.token_hex(32)  # 32 bytes = 256 bits


app = Flask(__name__)
app.secret_key = "02314abf9903e5a1f36900a216192341"
JWT_SECRET_KEY = "5ce6aa6eba51add6e67458f420e116681636a36e9fba02e862bf389a72f59638"

# Set up a folder for file uploads
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'jpg', 'jpeg', 'png', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def is_admin():
    user_email = session.get("email")  # Assuming email is stored in session
    return user_email == "lakshita@example.com"  # Only this email is admin

# Function to create a JWT token
def generate_jwt(user_id, username):
    """Generate a JWT token."""
    expiration_time = datetime.utcnow() + timedelta(hours=1)
    payload = {
        'user_id': user_id,
        'username': username,
        'exp': expiration_time
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm='HS256')

@app.context_processor
def inject_user():
    try:
        # Verify JWT token in cookies (if present)
        user_id = session.get("user_id")  # Get the logged-in user ID
        admin = is_admin()
        if not user_id:
            user = redirect(url_for('login'))
        print("Injecting user:", user_id)  # Debugging line
    except Exception as e:
        user = None
    
    return {"user": user_id,"admin":admin}

def ai_generate(prompt, max_tokens=1024):
    """Handles AI response generation with a token limit."""
    response = ollama.generate(model='llama3.2', prompt=prompt, options={"max_tokens": max_tokens})
    return response.get('response', '').strip()

@app.route('/api/register', methods=['POST'])
def register():
    """API Endpoint for user registration."""
    try:
        # Get data from the request body
        data = request.get_json()

        # Extract details from JSON data
        user_name = data.get('user_name')
        email = data.get('email')
        password = data.get('password')

        # Validate the input data
        if not user_name or not email or not password:
            return jsonify({"error": "Missing required fields: user_name, email, password"}), 400

        # Hash the password (you can use bcrypt or a more secure method for hashing passwords)
        hash_password = hashlib.sha256(password.encode()).hexdigest()

        # Register the user
        if register_insert(user_name, email, hash_password):
            return jsonify({"message": "User registered successfully!"}), 201
        else:
            return jsonify({"error": "Failed to register user."}), 500

    except Exception as err:
        print(f"Error: {err}")
        return jsonify({"error": "Something went wrong!"}), 500



@app.route('/api/login', methods=['POST'],endpoint="/api/login")
def login():
    """API endpoint for user login."""
    data = request.get_json()

    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    user = authenticate_user(email, password)
    if user:
        # Create Flask session
        session['user_id'] = user[0]  # Store user_id in session
        session['username'] = user[1]  # Store username in session
        session['email'] = user[2]  # Store email in session

        # Generate JWT token
        token = generate_jwt(user[0], user[1])

        # Log session data (for debugging)
        print(f"Session Data: {session}")

        return jsonify({
            "message": "Login successful!",
            "token": token  # Send JWT token to the client
        }), 200
    else:
        return jsonify({"error": "Invalid email or password"}), 401


@app.route('/api/check-session', methods=['GET'])
def check_session():
    """API endpoint to verify session and JWT token."""
    
    # Check Flask session
    if 'user_id' in session:
        return jsonify({
            "message": "Session is valid!",
            "user_id": session['user_id'],
            "username": session['username'],
            "email": session['email']
        }), 200

    # Check JWT token if not using Flask session
    token = request.headers.get('Authorization')
    print(token)
    if token:
        try:
            # Remove the 'Bearer ' prefix
            token = token.split(" ")[1]
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])

            # If JWT is valid, send user data
            return jsonify({
                "message": "JWT is valid!",
                "user_id": payload['user_id'],
                "username": payload['username']
            }), 200
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "JWT token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid JWT token"}), 401

    return jsonify({"error": "No valid session or JWT token found"}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    """API endpoint to log the user out by clearing the session."""
    session.clear()  # Clear the Flask session
    return jsonify({"message": "Successfully logged out!"}), 200



@app.route('/api/add-clothing', methods=['POST'])
def add_clothing():
    if 'image_url' not in request.files:
        return jsonify({"error": "Image file is required"}), 400

    file = request.files['image_url']
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({"error": "Invalid image file"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join("uploads/", filename)
    file.save(filepath)

    # Get other form fields
    category_id = request.form.get("category_id")
    occasion_id = request.form.get("occasion_id")
    season_id = request.form.get("season_id")
    description = request.form.get("description")
    user_id = request.form.get("user_id")
    gender = request.form.get("gender")
    if not all([category_id, occasion_id, season_id, description, user_id,gender]):
        print([category_id, occasion_id, season_id, description, user_id,gender])
        return jsonify({"error": "All fields are required"}), 400

    # Save to DB
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO clothing (image_url, category_id, occasion_id, season_id, description, user_id,gender)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (filename, category_id, occasion_id, season_id, description, user_id,gender))
    clothing_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return jsonify({"message": "Clothing added successfully", "clothing_id": clothing_id,"user_id":user_id})
    

@app.route("/api/generate-insights/<int:clothing_id>/<int:user_id>",methods=["POST"])
def generate_insights(clothing_id,user_id):
    conn = get_db_connection()
    print(clothing_id)
    clothing = conn.execute("""
    SELECT c.clothing_id, c.user_id, c.image_url, c.category_id, 
           c.occasion_id, c.season_id, c.description, c.gender, 
           c.created_at, 
           cat.category_name, o.occasion_name, s.season_name
    FROM clothing c
    JOIN categories cat ON c.category_id = cat.category_id
    JOIN occasions o ON c.occasion_id = o.occasion_id
    JOIN seasons s ON c.season_id = s.season_id
    WHERE c.clothing_id = ?
""", (clothing_id,)).fetchone()
    conn.close()
    
    if clothing is None:
        return jsonify({"error": "Clothing item not found"}), 404

    gender = ""
    if clothing['gender'] == 'M':
        gender +=  "Male"
    else:
        gender += "FeMale"
    prompt = f"""
    A user uploaded a clothing item with the following details:
    - Category: {clothing['category_name']}
    - Occasion: {clothing['occasion_name']}
    - Season: {clothing['season_name']}
    - Description: {clothing['description']}
    - Gender :{gender}

    Based on this, provide sustainable fashion advice, restyling tips, and complementary outfit suggestions. 
    """

    ai_response = ai_generate(prompt)
    fetch_image = fetch_and_store_images(query=clothing['description']+f"i want ot buy  {clothing['category_name']} picture of cloth which is sustainable eco friendly clothes for {gender}",user_id=user_id)
    print(ai_response)
    return jsonify({"insights": ai_response,"pictures":fetch_image})


@app.route('/api/add-category', methods=['POST'])
def add_category():
    data = request.get_json()

    category_name = data.get('category_name')

    if not category_name:
        return jsonify({"error": "Category name is required"}), 400

    # Call the insert_category function to add the category
    result = insert_category(category_name)

    return jsonify(result), 201

    
@app.route('/api/insert-occasion', methods=['POST'])
def api_insert_occasion():
    """API endpoint to insert an occasion."""
    data = request.get_json()  # Get the JSON data from the request
    
    occasion_name = data.get('occasion_name')

    # Check if occasion_name is provided
    if not occasion_name:
        return jsonify({"error": "Occasion name is required"}), 400

    # Insert the occasion into the database
    occasion_id = insert_occasion(occasion_name)

    # If the insert was successful, return the occasion ID
    if occasion_id:
        return jsonify({"message": "Occasion created successfully!", "occasion_id": occasion_id}), 201
    else:
        return jsonify({"error": "Failed to create occasion"}), 500
    
@app.route('/api/add-season', methods=['POST'])
def add_season():
    try:
        data = request.get_json()

        # Get season name from the request
        season_name = data.get('season_name')

        if not season_name:
            return jsonify({"error": "Season name is required"}), 400
        
        # Insert the season into the database
        season_id = insert_season(season_name)
        
        if season_id:
            return jsonify({"message": "Season added successfully!", "season_id": season_id}), 201
        else:
            return jsonify({"error": "Failed to add season"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

#CART API'S
# Add item to cart
@app.route('/cart', methods=['POST'])
def add_to_cart():
    data = request.json
    image_id = data.get('image_id')  # Optional
    image_url = data.get('image_url')  # Optional
    quantity = data.get('quantity', 1)
    price = data.get('price', 1000)
    if not image_id and not image_url:
        return jsonify({'error': 'Either image_id or image_url is required'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    # Validate image_id if provided
    if image_id:
        cursor.execute("SELECT id FROM images WHERE id = ?", (image_id,))
        image_record = cursor.fetchone()
        if not image_record:
            conn.close()
            return jsonify({'error': 'Invalid Image ID'}), 404

    # Insert into cart (image_id OR image_url)
    cursor.execute("INSERT INTO cart (image_id, image_url, quantity , price) VALUES (?, ?, ? , ?)", 
                   (image_id, image_url, quantity ,price))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Item added to cart'}), 201


# Get all cart items
@app.route('/cart', methods=['GET'])
def get_cart():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM cart")
    items = cursor.fetchall()
    conn.close()

    return jsonify([dict(item) for item in items])

# Update cart item quantity
@app.route('/cart/<int:item_id>', methods=['PUT'])
def update_cart(item_id):
    data = request.json
    quantity = data.get('quantity')

    if quantity is None or quantity <= 0:
        return jsonify({'error': 'Quantity must be greater than 0'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if cart item exists
    cursor.execute("SELECT id FROM cart WHERE id = ?", (item_id,))
    cart_item = cursor.fetchone()

    if not cart_item:
        conn.close()
        return jsonify({'error': 'Cart item not found'}), 404

    # Update quantity
    cursor.execute("UPDATE cart SET quantity = ? WHERE id = ?", (quantity, item_id))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Cart updated successfully'})


# Delete item from cart
@app.route('/cart/<int:item_id>', methods=['DELETE'])
def delete_from_cart(item_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM cart WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Item removed from cart'})

#CheckOut API
@app.route('/checkout', methods=['POST'])
def checkout():
    try:
        data = request.json

        # Validate required fields
        user_id = data.get('user_id')
        cart_items = data.get('cart_items')  # List of {image_id, quantity, price}
        payment_method = data.get('payment_method')  # "Online" or "COD"
        shipping_address = data.get('shipping_address')
        print("CART ITEMS: ",cart_items)
        if not all([user_id, cart_items, payment_method, shipping_address]):
            return jsonify({"error": "All fields (user_id, cart_items, payment_method, shipping_address) are required!"}), 400

        if not isinstance(cart_items, list) or not cart_items:
            return jsonify({"error": "Invalid cart items!"}), 400

        # Validate each cart item
        for item in cart_items:
            if not all(k in item for k in ('image_id', 'quantity', 'price')) or not isinstance(item['quantity'], int) or item['quantity'] <= 0:
                return jsonify({"error": "Each cart item must have a valid image_id, quantity (>0), and price!"}), 400

        # Calculate total price
        total_price = sum(item['price'] * item['quantity'] for item in cart_items)

        # Determine payment status
        payment_status = "Paid" if payment_method == "Online" else "Unpaid"

        # Database connection
        conn = get_db_connection()
        cursor = conn.cursor()

        # Insert order into the orders table
        cursor.execute('''
            INSERT INTO orders (user_id, total_price, status, payment_method, payment_status, shipping_address)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, total_price, "Pending", payment_method, payment_status, shipping_address))

        order_id = cursor.lastrowid  # Get the new order ID
        # Insert each cart item into order_items table
        for item in cart_items:
            cursor.execute('''
                INSERT INTO order_items (order_id, image_id, quantity, price)
                VALUES (?, ?, ?, ?)
            ''', (order_id, item['image_id'], item['quantity'], item['price']))

        # Commit changes and close connection
        conn.commit()
        conn.close()

        return jsonify({"success": True, "message": "Order placed successfully!", "order_id": order_id})

    except Exception as e:
        print("Error:", e)
        return jsonify({"error": str(e)}), 500

    finally:
        if 'conn' in locals():
            conn.close()  # Ensure connection is closed even on failure


@app.route('/orders/<int:user_id>', methods=['GET'])
def get_user_orders(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE user_id = ?", (user_id,))
    orders = cursor.fetchall()
    conn.close()

    return jsonify([dict(order) for order in orders])



"""  ----------------------------------------            NORMAL TEMPLATES ENDPOINT     ----------------------------------------                                  """
@app.route("/",endpoint="home")
def home():
    return render_template("home.html")

@app.route('/checkout')
def checkout_page():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT c.id, c.quantity, c.image_id ,i.image, i.price 
        FROM cart c
        JOIN images i ON c.image_id = i.id
    ''')
    
    cart_items = cursor.fetchall()
    conn.close()

    # Convert rows to dictionaries
    cart_items = [dict(item) for item in cart_items]
    print(cart_items)
    # Calculate total price
    total_price = sum(item["price"] * item["quantity"] for item in cart_items)

    return render_template('checkout.html', cart_items=cart_items, total_price=total_price)


# ✅ Admin API to Approve/Reject Orders
@app.route("/admin/orders/update", methods=["POST"])
def update_order_status():
    if not is_admin():
        return jsonify({"error": "Unauthorized"}), 403  # Return 403 if not admin

    data = request.json
    order_id = data.get("order_id")
    new_status = data.get("status")

    if new_status not in ["Approved", "Rejected"]:
        return jsonify({"error": "Invalid status"}), 400  # Return 400 for invalid status

    conn = get_db_connection()
    cursor = conn.cursor()

    # ✅ Update order status in database
    cursor.execute("UPDATE orders SET status = ? WHERE order_id = ?", (new_status, order_id))
    conn.commit()
    conn.close()

    return jsonify({"message": f"Order {order_id} updated to {new_status}"}), 200

@app.route("/orders")
def orders():
    user_id = session.get("user_id")  # Get the logged-in user ID
    if not user_id:
        return redirect(url_for("login"))  # Redirect if not logged in

    conn = get_db_connection()
    cursor = conn.cursor()

    # ✅ Fetch user orders
    cursor.execute('''
        SELECT o.order_id, o.ordered_at, o.total_price, o.status, o.payment_method
        FROM orders o
        WHERE o.user_id = ?
        ORDER BY o.ordered_at DESC
    ''', (user_id,))

    user_orders = cursor.fetchall()

    orders_with_items = []
    
    for order in user_orders:
        order_dict = dict(order)
        
        # ✅ Convert `ordered_at` to datetime object
        order_dict["ordered_at"] = datetime.strptime(order_dict["ordered_at"], "%Y-%m-%d %H:%M:%S")

        # ✅ Fetch order items with debugging prints
        cursor.execute('''
            SELECT oi.quantity, i.id AS image_id, i.image
            FROM order_items oi
            JOIN images i ON oi.image_id = i.id  -- ✅ Correct JOIN
            WHERE oi.order_id = ?
        ''', (order["order_id"],))

        order_items = cursor.fetchall()
        print(f"Order Items for order_id {order['order_id']}: {order_items}")

        # ✅ Ensure items is always a list
        order_dict["items"] = [dict(item) for item in order_items] if order_items else []

        orders_with_items.append(order_dict)

    conn.close()
    print(orders_with_items)
    # ✅ Check before accessing first item
    if orders_with_items and orders_with_items[0]["items"]:
        items_list = orders_with_items[0]["items"][0]
        print("First item:", items_list)
    else:
        print("No items found for this order.")
        items_list = None  # Handle case where no items exist

    return render_template("orders.html", orders=orders_with_items)

@app.route("/clothes", methods=["GET", "POST"], endpoint="clothes")
def clothes():
    if request.method == "GET":
        user_id = session.get("user_id")  # Get the logged-in user ID
        if not user_id:
            return redirect(url_for("login"))  # Redirect if not logged in

        conn = get_db_connection()
        cursor = conn.cursor()

        # Fetch categories, occasions, seasons
        cursor.execute("SELECT * FROM categories")
        categories = cursor.fetchall()

        cursor.execute("SELECT * FROM occasions")
        occasions = cursor.fetchall()

        cursor.execute("SELECT * FROM seasons")
        seasons = cursor.fetchall()

        conn.close()
        print(seasons)

        return render_template("clothes.html", categories=categories, occasions=occasions, seasons=seasons)
    
    if request.method == "POST":
        # Process file upload and form here
        pass

@app.route("/login",endpoint="login")
def login():
    return render_template("login.html")

@app.route("/signup",endpoint="signup")
def signup():
    return render_template("sign_up.html")

@app.route("/about",endpoint="about")
def signup():
    return render_template("about.html")

# ✅ Admin Route to Manage Orders
@app.route("/admin/orders",endpoint="admin-orders")
def admin_orders():
    if not is_admin():
        return redirect(url_for("login"))  # Redirect if not an admin

    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch all orders
    cursor.execute('''
        SELECT o.order_id, o.ordered_at, o.total_price, o.status, u.email
        FROM orders o
        JOIN users u ON o.user_id = u.user_id
        ORDER BY o.ordered_at DESC
    ''')
    orders = cursor.fetchall()

    conn.close()
    return render_template("admin_orders.html", orders=orders)

# ✅ Admin Route to Manage Orders
@app.route("/admin/manage",endpoint="admin-manage")
def admin_orders():
    if not is_admin():
        return redirect(url_for("login"))  # Redirect if not an admin

    return render_template("admin_manage.html")


@app.route('/render_insights', methods=["GET"])
def render_insights():
    # ✅ Get clothing_id as an Integer
    clothing_id = request.args.get("clothing_id")
    user_id = request.args.get("user_id")

    if not clothing_id or not user_id:
        return jsonify({"error": "Clothing ID and User ID are required"}), 400
    
    clothing_id = int(clothing_id)
    user_id = int(user_id)

    print(f"🔍 Debug: Received clothing_id={clothing_id}, user_id={user_id}")

    # ✅ Connect to the database
    conn = get_db_connection()
    cursor = conn.cursor()

    # ✅ Check if clothing exists
    cursor.execute("SELECT COUNT(*) FROM clothing WHERE clothing_id = ?", (clothing_id,))
    exists = cursor.fetchone()[0]

    if exists == 0:
        conn.close()
        return jsonify({"error": f"Clothing ID {clothing_id} does not exist"}), 404

    # ✅ Fetch clothing details
    clothing = cursor.execute("""
        SELECT c.clothing_id, c.user_id, c.image_url, c.category_id, 
               c.occasion_id, c.season_id, c.description, c.gender, 
               c.created_at, 
               cat.category_name, o.occasion_name, s.season_name
        FROM clothing c
        LEFT JOIN categories cat ON c.category_id = cat.category_id
        LEFT JOIN occasions o ON c.occasion_id = o.occasion_id
        LEFT JOIN seasons s ON c.season_id = s.season_id
        WHERE c.clothing_id = ?
    """, (clothing_id,)).fetchone()
    
    print("🔍 Debug: Fetched Clothing:", clothing)
    
    if clothing is None:
        conn.close()
        return jsonify({"error": "Clothing item not found"}), 404

    # ✅ Convert gender
    gender = "Male" if clothing["gender"] == "M" else "Female"

    # ✅ Generate AI insights
    prompt = f"""
    A user uploaded a clothing item with the following details:
    - **Category:** {clothing['category_name']}
    - **Occasion:** {clothing['occasion_name']}
    - **Season:** {clothing['season_name']}
    - **Description:** {clothing['description']}
    - **Gender:** {gender}

    Based on this, provide **sustainable fashion advice, restyling tips, and complementary outfit suggestions**. 
    """
    ai_response = ai_generate(prompt)

    # ✅ Fetch relevant images
    fetch_image = fetch_and_store_images(
        query=f"{clothing['description']} eco-friendly {clothing['category_name']} for {gender}",
        user_id=user_id
    )
    
    print(f"🔍 Debug: Fetch Image Batch ID = {fetch_image[0]}")

    cursor.execute("SELECT * FROM images WHERE batch_id = ?",(fetch_image[0],))
    images = cursor.fetchall()
    print(images[:4])
    conn.close()

    return render_template(
        "insights.html",
        insight=markdown.markdown(ai_response),
        images=images,
        clothing=clothing,
        user_id=user_id
    )




@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if the email exists
        cursor.execute("SELECT user_id FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()

        if user:
            user_id = user['user_id']
            reset_token = secrets.token_urlsafe(32)  # Generate a secure reset token
            expiry_time = datetime.utcnow() + timedelta(hours=1)  # Expires in 1 hour

            # Store token in password_resets table
            cursor.execute('''
                INSERT INTO password_resets (user_id, reset_token, reset_token_expiry)
                VALUES (?, ?, ?)
            ''', (user_id, reset_token, expiry_time))

            conn.commit()
            conn.close()

            # In a real app, send an email with this link
            reset_link = url_for('reset_password', token=reset_token, _external=True)
            flash(f"Password reset link: {reset_link}", "info")

        else:
            flash("Email not found!", "danger")

    return render_template('forgot_password.html')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if the token exists and is still valid
    cursor.execute('''
        SELECT user_id, reset_token_expiry FROM password_resets WHERE reset_token = ?
    ''', (token,))
    
    reset_entry = cursor.fetchone()

    if not reset_entry:
        flash("Invalid or expired token!", "danger")
        return redirect(url_for('forgot_password'))

    expiry_time = reset_entry["reset_token_expiry"]
    if datetime.utcnow() > datetime.strptime(expiry_time, '%Y-%m-%d %H:%M:%S.%f'):

        flash("Token has expired!", "danger")
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        new_password = request.form['password']
        hashed_password = hashlib.sha256(new_password.encode()).hexdigest()

        # Update user password
        user_id = reset_entry["user_id"]
        cursor.execute("UPDATE users SET password = ? WHERE user_id = ?", (hashed_password, user_id))

        # Remove token after successful reset
        cursor.execute("DELETE FROM password_resets WHERE reset_token = ?", (token,))
        
        conn.commit()
        conn.close()
        
        flash("Password reset successfully! You can now log in.", "success")
        return redirect(url_for('login'))

    return render_template('reset_password.html')
if __name__ == '__main__':
    app.run(debug=True)