import os
import requests
from flask import Flask, render_template, request, redirect, url_for
from bs4 import BeautifulSoup
import sqlite3
import random
import pytesseract
from PIL import Image
from io import BytesIO
from urllib.parse import urljoin, urlparse
import re

app = Flask(__name__)

# Database setup
def init_db():
    conn = sqlite3.connect('poems.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS poems
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  poet_name TEXT,
                  poem_text TEXT,
                  source_url TEXT,
                  UNIQUE(poet_name, poem_text))''')
    conn.commit()
    conn.close()

def get_poems_count(poet_name):
    conn = sqlite3.connect('poems.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM poems WHERE poet_name=?", (poet_name,))
    count = c.fetchone()[0]
    conn.close()
    return count

def save_poem_to_db(poet_name, poem_text, source_url):
    conn = sqlite3.connect('poems.db')
    c = conn.cursor()
    try:
        c.execute("INSERT OR IGNORE INTO poems (poet_name, poem_text, source_url) VALUES (?, ?, ?)",
                  (poet_name, poem_text, source_url))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    finally:
        conn.close()

def get_existing_poems(poet_name):
    conn = sqlite3.connect('poems.db')
    c = conn.cursor()
    c.execute("SELECT poem_text FROM poems WHERE poet_name=?", (poet_name,))
    poems = [row[0] for row in c.fetchall()]
    conn.close()
    return poems

def extract_text_from_image(image_url):
    """Extract text from image using OCR"""
    try:
        # Download image
        response = requests.get(image_url)
        img = Image.open(BytesIO(response.content))
        
        # Use pytesseract to extract text
        text = pytesseract.image_to_string(img, lang='urd')
        return text.strip()
    except Exception as e:
        print(f"Error extracting text from image: {e}")
        return ""

def scrape_urdu_poems(url, poet_name):
    """Scrape Urdu poems from the given URL"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for common elements that might contain poems
        # This is a basic implementation - would need to be adapted for specific sites
        poems = []
        
        # Look for divs with common class names for poetry
        poem_elements = soup.find_all(['div', 'p', 'blockquote'], 
                                    class_=re.compile(r'poem|shair|sher|verse|poetry|ghazal|nazm', re.I))
        
        for element in poem_elements:
            text = element.get_text().strip()
            if len(text) > 50:  # Filter out very short texts
                poems.append(text)
        
        # Also look for all paragraphs that might be poems
        paragraphs = soup.find_all('p')
        for p in paragraphs:
            text = p.get_text().strip()
            # Basic heuristic: if text contains Urdu characters and seems poem-like
            if any('\u0600' <= char <= '\u06FF' for char in text) and len(text) > 50:
                poems.append(text)
        
        # Look for images that might contain poems
        images = soup.find_all('img')
        for img in images:
            img_src = img.get('src') or img.get('data-src')
            if img_src:
                img_url = urljoin(url, img_src)
                # Check if image likely contains text (by filename or other heuristics)
                if any(ext in img_url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif']):
                    ocr_text = extract_text_from_image(img_url)
                    if ocr_text and len(ocr_text) > 50:
                        poems.append(ocr_text)
        
        return poems
    
    except Exception as e:
        print(f"Error scraping poems: {e}")
        return []

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        poet_name = request.form['poet_name']
        website_url = request.form['website_url']
        
        if not poet_name or not website_url:
            return render_template('index.html', error="Both poet name and website URL are required.")
        
        # Get poems already stored in DB to avoid duplicates
        existing_poems = get_existing_poems(poet_name)
        
        # Scrape poems from website
        scraped_poems = scrape_urdu_poems(website_url, poet_name)
        
        # Filter out poems already in DB
        new_poems = [poem for poem in scraped_poems if poem not in existing_poems]
        
        if new_poems:
            # Select a random poem
            selected_poem = random.choice(new_poems)
            
            # Save the selected poem to DB
            save_poem_to_db(poet_name, selected_poem, website_url)
            
            return render_template('poem.html', poet_name=poet_name, poem=selected_poem)
        else:
            return render_template('index.html', error="No new poems found or all poems already stored.")
    
    return render_template('index.html')

if __name__ == '__main__':
    init_db()
    app.run(debug=True)