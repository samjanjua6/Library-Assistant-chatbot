import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from .model import Book, Loan
from ..core.database import SessionLocal


# --- Pydantic Models for Tools ---

class SearchBooksArgs(BaseModel):
    query: str = Field(..., description="The title, author, or genre to search for")

class CheckAvailabilityArgs(BaseModel):
    book_id: int = Field(..., description="The ID of the book to check")

class BorrowBookArgs(BaseModel):
    user_id: int = Field(..., description="The ID of the user borrowing the book")
    book_id: int = Field(..., description="The ID of the book to borrow")

class ReturnBookArgs(BaseModel):
    user_id: int = Field(..., description="The ID of the user returning the book")
    book_id: int = Field(..., description="The ID of the book to return")

class GetBorrowedBooksArgs(BaseModel):
    user_id: int = Field(..., description="The ID of the user whose borrowed books to retrieve")


# --- Plain Python Functions (Tool Implementations) ---

def search_books(args: SearchBooksArgs) -> str:
    """Search for books by title, author, or genre."""
    db = SessionLocal()
    try:
        q = f"%{args.query}%"
        books = db.query(Book).filter(
            (Book.title.ilike(q)) | (Book.author.ilike(q)) | (Book.genre.ilike(q))
        ).all()
        
        if not books:
            return json.dumps({"status": "no_results", "message": f"No books found matching '{args.query}'."})
        
        results = [
            {
                "id": b.id,
                "title": b.title,
                "author": b.author,
                "available_copies": b.available_copies
            } for b in books
        ]
        return json.dumps({"status": "success", "results": results})
    finally:
        db.close()


def check_availability(args: CheckAvailabilityArgs) -> str:
    """Check availability of a specific book by ID."""
    db = SessionLocal()
    try:
        book = db.query(Book).filter(Book.id == args.book_id).first()
        if not book:
            return json.dumps({"status": "error", "message": "Book not found."})
        
        return json.dumps({
            "status": "success",
            "title": book.title,
            "available_copies": book.available_copies,
            "total_copies": book.total_copies
        })
    finally:
        db.close()


def borrow_book(args: BorrowBookArgs) -> str:
    """Borrow a book, enforcing max 3 active loans and available copy checks."""
    db = SessionLocal()
    try:
        # Check active loans limit
        active_loans_count = db.query(Loan).filter(
            Loan.user_id == args.user_id,
            Loan.status == "borrowed"
        ).count()
        
        if active_loans_count >= 3:
            return json.dumps({
                "status": "failure",
                "reason": "User has reached the maximum limit of 3 borrowed books."
            })
            
        # Check if user already borrowed this specific book
        existing_loan = db.query(Loan).filter(
            Loan.user_id == args.user_id,
            Loan.book_id == args.book_id,
            Loan.status == "borrowed"
        ).first()
        
        if existing_loan:
            return json.dumps({
                "status": "failure",
                "reason": "User has already borrowed this book and has not returned it yet."
            })

        # Check stock
        book = db.query(Book).filter(Book.id == args.book_id).first()
        if not book:
            return json.dumps({"status": "error", "message": "Book not found."})
            
        if book.available_copies <= 0:
            return json.dumps({
                "status": "failure",
                "reason": f"No available copies for '{book.title}'."
            })
            
        # Execute borrow
        book.available_copies -= 1
        
        due_date = datetime.utcnow() + timedelta(days=14)
        new_loan = Loan(
            book_id=book.id,
            user_id=args.user_id,
            due_date=due_date,
            status="borrowed"
        )
        db.add(new_loan)
        db.commit()
        
        return json.dumps({
            "status": "success",
            "message": f"Successfully borrowed '{book.title}'.",
            "due_date": due_date.isoformat()
        })
    except Exception as e:
        db.rollback()
        return json.dumps({"status": "error", "message": str(e)})
    finally:
        db.close()


def return_book(args: ReturnBookArgs) -> str:
    """Return a book by updating the loan and incrementing stock."""
    db = SessionLocal()
    try:
        loan = db.query(Loan).filter(
            Loan.user_id == args.user_id,
            Loan.book_id == args.book_id,
            Loan.status == "borrowed"
        ).first()
        
        if not loan:
            return json.dumps({
                "status": "failure",
                "reason": "Active loan for this book not found for the user."
            })
            
        book = db.query(Book).filter(Book.id == args.book_id).first()
        
        loan.status = "returned"
        loan.returned_at = datetime.utcnow()
        if book:
            book.available_copies += 1
            
        db.commit()
        return json.dumps({
            "status": "success",
            "message": f"Successfully returned book ID {args.book_id}."
        })
    except Exception as e:
        db.rollback()
        return json.dumps({"status": "error", "message": str(e)})
    finally:
        db.close()


def get_my_borrowed_books(args: GetBorrowedBooksArgs) -> str:
    """Get a list of active loans for the user."""
    db = SessionLocal()
    try:
        loans = db.query(Loan).filter(
            Loan.user_id == args.user_id,
            Loan.status == "borrowed"
        ).all()
        
        if not loans:
            return json.dumps({"status": "success", "results": []})
            
        results = [
            {
                "loan_id": loan.id,
                "book_id": loan.book_id,
                "title": loan.book.title,
                "borrowed_at": loan.borrowed_at.isoformat(),
                "due_date": loan.due_date.isoformat()
            } for loan in loans
        ]
        
        return json.dumps({"status": "success", "results": results})
    finally:
        db.close()
