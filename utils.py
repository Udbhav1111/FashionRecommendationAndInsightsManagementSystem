import sqlite3
import requests
import base64
import uuid
from serpapi import GoogleSearch
from datetime import datetime
import random

SERP_API_KEY = "c3ea8163a812791af7f0cfc5a4bbc7db2bbc7bdfca7ced8a2778b054221681f6"

# Connect to SQLite
conn = sqlite3.connect("fashion_sense.sqlite3", check_same_thread=False)
cursor = conn.cursor()

# Define blocked domains
BLOCKED_DOMAINS = ["tiktok.com", "example_blocked.com"]  # Add more if needed

def is_blocked_url(url):
    """Check if the URL belongs to a blocked domain."""
    return any(blocked in url for blocked in BLOCKED_DOMAINS)

def generate_price():
    return round(random.uniform(800, 1200), 2)  # Generates a price with two decimal places

def fetch_images_with_serpapi(query, num=2):
    """Fetch image URLs from SerpAPI."""
    params = {
        "engine": "google",
        "q": query,
        "tbm": "isch",  # Image search
        "num": num,
        "api_key": SERP_API_KEY  # 🔑 Get free API key from https://serpapi.com
    }

    search = GoogleSearch(params)
    results = search.get_dict()
    images = results.get("images_results", [])

    return [img["original"] for img in images if "original" in img]  # Extract only valid image URLs

def fetch_and_store_images(query, user_id, num_images=2):
    """Fetch images from SerpAPI, store links in DB, and return batch_id and full image objects."""

    batch_id = str(uuid.uuid4())  # Generate a unique batch ID

    # Fetch image URLs
    image_urls = fetch_images_with_serpapi(query, num_images)
    print(image_urls)
    for image_url in image_urls:
        if not image_url:
            continue  # Skip empty URLs

        # Skip TikTok links
        if "tiktok.com" in image_url:
            print(f"Skipping TikTok link: {image_url}")
            continue  # Skip the image URL if it's from TikTok

        try:
            random_price = generate_price()
            # Save the image URL directly in the database
            cursor.execute(''' 
                INSERT INTO images (user_id, query, image, batch_id, price ,created_at) 
                VALUES (?, ?, ?, ?, ? , ?)
            ''', (user_id, query, image_url, batch_id,random_price, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()

        except sqlite3.Error as e:
            print(f"Database error: {e}")

    # Fetch all stored image objects for this batch
    cursor.execute(''' 
        SELECT * FROM images WHERE batch_id = ? 
    ''', (batch_id,))
    image_objects = cursor.fetchall()  # Fetch full records as a list of tuples

    return [batch_id, image_objects]



