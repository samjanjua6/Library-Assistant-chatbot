import json
import urllib.request
from app.core.database import SessionLocal
from app.library.model import Book
from app.users.model import User
import random

def seed_1000_books():
    db = SessionLocal()
    existing_count = db.query(Book).count()
    if existing_count >= 1000:
        print(f"Already have {existing_count} books. Skipping.")
        db.close()
        return
        
    print("Fetching 1000 popular books from OpenLibrary API (this might take 5-10 seconds)...")
    url = "https://openlibrary.org/search.json?q=bestseller&limit=1000&sort=editions"
    
    req = urllib.request.Request(url, headers={'User-Agent': 'ZyloLibraryApp/1.0'})
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
    except Exception as e:
        print(f"Failed to fetch from OpenLibrary: {e}")
        db.close()
        return
        
    books_data = data.get('docs', [])
    print(f"Successfully fetched {len(books_data)} books from API! Seeding into database...")
    
    books_to_insert = []
    # Use a set to prevent duplicate titles
    seen_titles = set()
    
    for item in books_data:
        title = item.get('title', 'Unknown Title')
        
        if title in seen_titles:
            continue
            
        seen_titles.add(title)
        
        authors = item.get('author_name', ['Unknown Author'])
        author = authors[0] if authors else 'Unknown Author'
        
        genres = item.get('subject', ['Fiction'])
        genre = genres[0] if genres else 'Fiction'
        
        copies = random.randint(2, 10)
        
        b = Book(
            title=title[:255],
            author=author[:255],
            genre=genre[:255],
            total_copies=copies,
            available_copies=copies
        )
        books_to_insert.append(b)
        
    try:
        db.add_all(books_to_insert)
        db.commit()
        print(f"Successfully inserted {len(books_to_insert)} unique books into the database! Your library is fully stocked!")
    except Exception as e:
        db.rollback()
        print(f"Error saving to database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_1000_books()
