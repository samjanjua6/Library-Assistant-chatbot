from __future__ import annotations
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import or_

from ..core.database import get_db
from ..core.deps import get_current_user, get_current_admin_user
from ..users.model import User
from .model import Book, Loan
from .service import return_book, ReturnBookArgs
from .rag import add_document_to_kb, clear_knowledge_base
router = APIRouter(tags=["Library"])

# --- Pydantic Schemas for Requests/Responses ---

class BookCreate(BaseModel):
    title: str
    author: str
    genre: Optional[str] = None
    total_copies: int = 1

class BookUpdate(BaseModel):
    total_copies: int
    available_copies: int


# --- User Endpoints ---

@router.get("/api/library/loans")
def get_my_loans(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Fetch all active loans for the current user."""
    loans = db.query(Loan).filter(
        Loan.user_id == user.id,
        Loan.status == "borrowed"
    ).all()
    
    results = []
    for loan in loans:
        results.append({
            "id": loan.id,
            "book_id": loan.book_id,
            "title": loan.book.title,
            "author": loan.book.author,
            "borrowed_at": loan.borrowed_at.isoformat(),
            "due_date": loan.due_date.isoformat(),
            "status": loan.status
        })
    return results


@router.post("/api/library/loans/{book_id}/return")
def api_return_book(book_id: int, user: User = Depends(get_current_user)):
    """Return a book by its book ID using the existing service function."""
    import json
    result_json = return_book(ReturnBookArgs(user_id=user.id, book_id=book_id))
    result = json.loads(result_json)
    if result.get("status") != "success":
        raise HTTPException(status_code=400, detail=result.get("reason") or result.get("message"))
    return {"success": True}


# --- Admin Endpoints ---

@router.get("/api/library/admin/books")
def admin_get_books(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db), 
    admin: User = Depends(get_current_admin_user)
):
    """Get all books with pagination and search."""
    query = db.query(Book)
    if search:
        query = query.filter(
            or_(
                Book.title.ilike(f"%{search}%"),
                Book.author.ilike(f"%{search}%")
            )
        )
    
    total = query.count()
    books = query.order_by(Book.id.desc()).offset(skip).limit(limit).all()
    
    return {
        "books": books,
        "total": total
    }


@router.post("/api/library/admin/books")
def admin_add_book(book_in: BookCreate, db: Session = Depends(get_db), admin: User = Depends(get_current_admin_user)):
    """Add a new book."""
    book = Book(
        title=book_in.title,
        author=book_in.author,
        genre=book_in.genre,
        total_copies=book_in.total_copies,
        available_copies=book_in.total_copies
    )
    db.add(book)
    db.commit()
    db.refresh(book)
    return book


@router.put("/api/library/admin/books/{book_id}")
def admin_update_book(book_id: int, book_in: BookUpdate, db: Session = Depends(get_db), admin: User = Depends(get_current_admin_user)):
    """Update inventory counts for a book."""
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    book.total_copies = book_in.total_copies
    book.available_copies = book_in.available_copies
    db.commit()
    db.refresh(book)
    return book


@router.get("/api/library/admin/loans")
def admin_get_all_loans(db: Session = Depends(get_db), admin: User = Depends(get_current_admin_user)):
    """Get all active loans across all users."""
    loans = db.query(Loan).filter(Loan.status == "borrowed").order_by(Loan.due_date.asc()).all()
    
    results = []
    for loan in loans:
        results.append({
            "id": loan.id,
            "book_id": loan.book_id,
            "title": loan.book.title,
            "user_id": loan.user_id,
            "username": loan.user.username,
            "borrowed_at": loan.borrowed_at.isoformat(),
            "due_date": loan.due_date.isoformat(),
            "status": loan.status
        })
    return results

@router.post("/api/library/admin/knowledge-base/upload")
async def admin_upload_kb(
    file: UploadFile = File(...),
    chunk_size: int = Form(1000),
    chunk_overlap: int = Form(200),
    admin: User = Depends(get_current_admin_user)
):
    """Upload a document to the knowledge base with dynamic chunking."""
    if not (file.filename.endswith(".txt") or file.filename.endswith(".pdf")):
        raise HTTPException(status_code=400, detail="Only .txt and .pdf files are supported.")
    
    content = await file.read()
    
    if file.filename.endswith(".pdf"):
        import io
        from pypdf import PdfReader
        pdf_file = io.BytesIO(content)
        reader = PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    else:
        text = content.decode("utf-8")
    
    try:
        add_document_to_kb(file.filename, text, chunk_size, chunk_overlap)
        return {"success": True, "message": f"Successfully ingested {file.filename}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/api/library/admin/knowledge-base")
def admin_clear_kb(admin: User = Depends(get_current_admin_user)):
    """Clear the knowledge base."""
    try:
        clear_knowledge_base()
        return {"success": True, "message": "Knowledge base cleared."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
