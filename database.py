import sqlite3

DB_PATH = "fashion_sense.sqlite3"  # Update with your desired database path

def create_tables():
    """Ensures the database tables exist."""
    with sqlite3.connect(DB_PATH) as db:
        cursor = db.cursor()
        # Create user_details table
        cursor.execute(''' 
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                first_name TEXT,
                last_name TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        ''')

        # Create categories table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                category_id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_name TEXT NOT NULL -- e.g., Shirt, Dress, Pants
            );
        ''')

        # Create occasions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS occasions (
                occasion_id INTEGER PRIMARY KEY AUTOINCREMENT,
                occasion_name TEXT NOT NULL -- e.g., Casual, Formal, Party
            );
        ''')

        # Create seasons table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS seasons (
                season_id INTEGER PRIMARY KEY AUTOINCREMENT,
                season_name TEXT NOT NULL -- e.g., Summer, Winter
            );
        ''')

        # Create clothing table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clothing (
                clothing_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                image_url TEXT NOT NULL,  -- URL of the uploaded clothing image
                category_id INTEGER NOT NULL,
                occasion_id INTEGER NOT NULL,
                season_id INTEGER NOT NULL,
                description TEXT,  -- Description for styling/upcycling
                gender TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (category_id) REFERENCES categories(category_id) ON DELETE CASCADE,
                FOREIGN KEY (occasion_id) REFERENCES occasions(occasion_id) ON DELETE CASCADE,
                FOREIGN KEY (season_id) REFERENCES seasons(season_id) ON DELETE CASCADE
            );
        ''')

        # Create recommendations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recommendations (
                recommendation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                clothing_id INTEGER NOT NULL,
                recommended_for TEXT,  -- Styling/upcycling suggestions
                ollama_response TEXT,  -- Response from Ollama (LLM)
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (clothing_id) REFERENCES clothing(clothing_id) ON DELETE CASCADE
            );
        ''')

        cursor.execute(''' 
            CREATE TABLE IF NOT EXISTS images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                query TEXT NOT NULL,
                image TEXT NOT NULL, -- Base64 image data
                batch_id TEXT NOT NULL, -- Unique batch ID per fetch
                price REAL NOT NULL, -- Price for the item
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Track when images were added
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            );
        ''')

        # Create cart table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cart (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_id INTEGER NOT NULL,  -- Reference to images table
                quantity INTEGER DEFAULT 1,
                price REAL NOT NULL,  -- Price per unit
                image_url TEXT NULL,
                added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (image_id) REFERENCES images(id) ON DELETE CASCADE
            );
        ''')
        # Orders Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                total_price REAL NOT NULL,  
                status TEXT DEFAULT 'Pending',  -- Order status (Pending, Shipped, Delivered, Canceled)
                payment_method TEXT NOT NULL,  -- 'Online' or 'Cash On Delivery'
                payment_status TEXT DEFAULT 'Unpaid',  -- 'Paid' or 'Unpaid'
                shipping_address TEXT NOT NULL,
                ordered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            );
        ''')
        cursor.execute(''' 
            CREATE TABLE IF NOT EXISTS order_items (
            order_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            image_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
            FOREIGN KEY (image_id) REFERENCES images(id) ON DELETE CASCADE
        );
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS password_resets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                reset_token TEXT NOT NULL,
                reset_token_expiry DATETIME NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            );
        ''')

        db.commit()
        print("Tables created successfully!")
create_tables()