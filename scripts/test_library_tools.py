import sys
import os
import json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.library.service import (
    search_books, SearchBooksArgs,
    check_availability, CheckAvailabilityArgs,
    borrow_book, BorrowBookArgs,
    return_book, ReturnBookArgs,
    get_my_borrowed_books, GetBorrowedBooksArgs
)
from app.users.model import User
from app.core.database import SessionLocal

def test_tools():
    db = SessionLocal()
    # Ensure there is a test user with ID 1
    user = db.query(User).filter(User.id == 1).first()
    if not user:
        user = User(id=1, email="test@test.com", username="testuser", full_name="Test User", hashed_password="pw")
        db.add(user)
        db.commit()
    db.close()

    print("--- 1. Search Books ---")
    print(search_books(SearchBooksArgs(query="Tolkien")))

    print("\n--- 2. Check Availability ---")
    print(check_availability(CheckAvailabilityArgs(book_id=1))) # Hobbit should be 0

    print("\n--- 3. Borrow Book (Out of stock test) ---")
    print(borrow_book(BorrowBookArgs(user_id=1, book_id=1)))

    print("\n--- 4. Borrow Book (Success) ---")
    print(borrow_book(BorrowBookArgs(user_id=1, book_id=2)))

    print("\n--- 5. Get Borrowed Books ---")
    print(get_my_borrowed_books(GetBorrowedBooksArgs(user_id=1)))

if __name__ == "__main__":
    test_tools()
