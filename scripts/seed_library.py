import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import SessionLocal, engine, Base
from app.library.model import Book

def seed():
    # Only creating tables here for safety, though they should already exist
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        if db.query(Book).count() > 0:
            print("Books already exist in the database. Seeding skipped.")
            return

        books = [
            Book(title="The Hobbit", author="J.R.R. Tolkien", genre="Fantasy", total_copies=3, available_copies=0), # Out of stock!
            Book(title="1984", author="George Orwell", genre="Dystopian", total_copies=5, available_copies=5),
            Book(title="To Kill a Mockingbird", author="Harper Lee", genre="Classic", total_copies=4, available_copies=4),
            Book(title="The Great Gatsby", author="F. Scott Fitzgerald", genre="Classic", total_copies=2, available_copies=2),
            Book(title="Dune", author="Frank Herbert", genre="Sci-Fi", total_copies=6, available_copies=6),
            Book(title="Pride and Prejudice", author="Jane Austen", genre="Romance", total_copies=3, available_copies=3),
            Book(title="The Catcher in the Rye", author="J.D. Salinger", genre="Fiction", total_copies=2, available_copies=2),
            Book(title="Fahrenheit 451", author="Ray Bradbury", genre="Dystopian", total_copies=4, available_copies=4),
            Book(title="Brave New World", author="Aldous Huxley", genre="Sci-Fi", total_copies=3, available_copies=3),
            Book(title="The Lord of the Rings", author="J.R.R. Tolkien", genre="Fantasy", total_copies=7, available_copies=7),
            Book(title="Harry Potter and the Sorcerer's Stone", author="J.K. Rowling", genre="Fantasy", total_copies=5, available_copies=5),
            Book(title="The Alchemist", author="Paulo Coelho", genre="Fiction", total_copies=4, available_copies=4)
        ]
        
        db.add_all(books)
        db.commit()
        print("Database seeded with books successfully!")
    except Exception as e:
        print("Error seeding database:", e)
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed()
