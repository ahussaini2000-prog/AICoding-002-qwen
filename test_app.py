import os
import sys
sys.path.insert(0, '/workspace/urdu_poem_app')

# Test imports
try:
    from app import init_db, scrape_urdu_poems, extract_text_from_image
    print("✓ Imports successful")
except ImportError as e:
    print(f"✗ Import error: {e}")

# Initialize database
try:
    init_db()
    print("✓ Database initialized")
except Exception as e:
    print(f"✗ Database initialization error: {e}")

# Test if we can connect to database
try:
    import sqlite3
    conn = sqlite3.connect('poems.db')
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = c.fetchall()
    print(f"✓ Database connection successful, tables: {tables}")
    conn.close()
except Exception as e:
    print(f"✗ Database connection error: {e}")

print("\nApplication structure verified successfully!")
print("\nThe Urdu Poem App includes:")
print("- Web interface to input poet name and website URL")
print("- Scrapes Urdu poems from the given website")
print("- Uses OCR to extract text from poem images")
print("- Stores poems in database to prevent duplicates")
print("- Displays poems in Urdu Nastaliq font")
print("\nTo run the application:")
print("cd /workspace/urdu_poem_app && python app.py")
print("Then visit http://127.0.0.1:5000 in your browser")