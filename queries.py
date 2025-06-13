from database import *
import hashlib
db = sqlite3.connect(DB_PATH)

def register_insert(username, email, hash_password, first_name=None, last_name=None):
    """Inserts a new user into the database."""
    try:
        with sqlite3.connect(DB_PATH) as db:
            cursor = db.cursor()
            cursor.execute(
                '''INSERT INTO users(username, email, password, first_name, last_name) 
                VALUES(?, ?, ?, ?, ?)''',
                (username, email, hash_password, first_name, last_name)
            )
            db.commit()
        return True
    except Exception as err:
        print("\n\nError Occurs: ", err)
        return False
    
def authenticate_user(email, password):
    """Simulate user authentication."""
    # Replace this with actual DB query
    with sqlite3.connect('fashion_sense.sqlite3') as db:
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        if user and hashlib.sha256(password.encode()).hexdigest() == user[3]:  # Assuming password is hashed in DB
            return user
    return None

def get_sustainable_guidelines(clothing_id):
    with sqlite3.connect(DB_PATH) as db:
        cursor = db.cursor()
        # Example logic for suggesting sustainable materials or upcycling ideas
        cursor.execute('SELECT category_id FROM clothing WHERE clothing_id = ?', (clothing_id,))
        category = cursor.fetchone()

        if category:
            category_id = category[0]
            
            # Example of a simple lookup based on the category (e.g., "Shirt")
            if category_id == 1:  # Assuming 1 is for Shirts
                return "Consider using organic cotton or upcycling old shirts into bags or accessories."

    return "No sustainable guidelines available for this category."

def insert_clothing_item(user_id, image_url, category_id, occasion_id, season_id, description):
    """Inserts a new clothing item into the clothing table."""
    try:
        # Use 'with' to manage the database connection context
        with sqlite3.connect(DB_PATH) as db:
            cursor = db.cursor()

            # Insert the clothing item into the database
            cursor.execute('''
                INSERT INTO clothing (user_id, image_url, category_id, occasion_id, season_id, description)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, image_url, category_id, occasion_id, season_id, description))

            # The 'with' statement automatically commits changes, so no need for db.commit()

            # Return the ID of the newly inserted clothing item
            return cursor.lastrowid
    except Exception as e:
        print(f"Error inserting clothing item: {e}")
        return None
    
def insert_category(category_name):
    """Insert a new category into the categories table."""
    with sqlite3.connect(DB_PATH) as db:
        cursor = db.cursor()

        # Insert the new category into the database
        cursor.execute('''
            INSERT INTO categories (category_name)
            VALUES (?)
        ''', (category_name,))
        
        # The context manager automatically commits the transaction when done.
        
    return {"message": "Category Created Successfully!"}


def insert_occasion(occasion_name):
    """Inserts a new occasion into the occasions table."""
    try:
        # Use 'with' to manage the database connection context
        with sqlite3.connect(DB_PATH) as db:
            cursor = db.cursor()

            # Insert the occasion into the database
            cursor.execute('''
                INSERT INTO occasions (occasion_name)
                VALUES (?)
            ''', (occasion_name,))

            # The 'with' statement automatically commits changes, so no need for db.commit()

            # Return the ID of the newly inserted occasion
            return cursor.lastrowid
    except Exception as e:
        print(f"Error inserting occasion: {e}")
        return None
    

def insert_season(season_name):
    """Inserts a new season into the seasons table."""
    try:
        # Use 'with' to manage the database connection context
        with sqlite3.connect(DB_PATH) as db:
            cursor = db.cursor()

            # Insert the season into the database
            cursor.execute(''' 
                INSERT INTO seasons (season_name) 
                VALUES (?) 
            ''', (season_name,))

            # The 'with' statement automatically commits changes, so no need for db.commit()

            # Return the ID of the newly inserted season
            return cursor.lastrowid
    except Exception as e:
        print(f"Error inserting season: {e}")
        return None

def test():
    try:
        # Use 'with' to manage the database connection context
        with sqlite3.connect(DB_PATH) as db:
            cursor = db.cursor()

            cursor.execute(''' 
                SELECT * FROM images WHERE batch_id = ? 
            ''', ("8a128ddb-99a4-4d04-8749-d50276762f18",))
            image_objects = cursor.fetchall()  # Fetch full records as a list of tuples

            # Return the ID of the newly inserted season
            return image_objects
    except Exception as e:
        print(f"Error inserting season: {e}")
        return None

    