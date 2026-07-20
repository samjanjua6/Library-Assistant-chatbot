from __future__ import annotations
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import or_
import shutil
from pathlib import Path
import subprocess

from ..core.database import get_db
from ..core.deps import get_current_user, get_current_admin_user
from ..users.model import User
from .model import Book, Loan
from .service import return_book, ReturnBookArgs
from .rag import (
    add_document_to_kb, delete_document, list_documents,
    clear_knowledge_base, extract_text, KNOWLEDGE_BASE_DIR, SUPPORTED_EXTENSIONS,
    ingest_documents
)

class ReingestPayload(BaseModel):
    chunk_size: int
    chunk_overlap: int

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


# ── Knowledge Base Endpoints ──────────────────────────────────────────────────

def sync_git_knowledge_base(action: str, filename: str):
    """
    Automatically commits and pushes a knowledge base file to GitHub.
    action: 'add' or 'rm'
    """
    try:
        # Run git commands synchronously
        cwd = str(Path(__file__).resolve().parent.parent.parent)
        filepath = f"knowledge_base/{filename}"
        
        if action == 'add':
            subprocess.run(["git", "add", filepath], cwd=cwd, check=True, capture_output=True)
            msg = f"Auto-add {filename} to knowledge base"
        else:
            subprocess.run(["git", "rm", filepath], cwd=cwd, check=True, capture_output=True)
            msg = f"Auto-remove {filename} from knowledge base"
            
        subprocess.run(["git", "commit", "-m", msg], cwd=cwd, check=True, capture_output=True)
        subprocess.run(["git", "push", "origin", "main"], cwd=cwd, check=True, capture_output=True)
        return True, ""
    except subprocess.CalledProcessError as e:
        error_output = e.stderr.decode().strip() if e.stderr else str(e)
        print(f"[Git Sync Error] {error_output}")
        return False, error_output
    except Exception as e:
        print(f"[Git Sync Error] Unexpected error: {e}")
        return False, str(e)


@router.get("/api/library/admin/knowledge-base")
def admin_list_kb(admin: User = Depends(get_current_admin_user)):
    """List all documents in the knowledge base."""
    return {"documents": list_documents()}


@router.post("/api/library/admin/knowledge-base/upload")
async def admin_upload_kb(
    file: UploadFile = File(...),
    chunk_size: int = Form(1000),
    chunk_overlap: int = Form(200),
    admin: User = Depends(get_current_admin_user)
):
    """
    Upload any supported document to the knowledge base and ingest it into ChromaDB.
    Supported: .txt, .pdf, .md, .docx, .csv, .json, .xlsx
    """
    ext = Path(file.filename).suffix.lower() if file.filename else ""
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )

    # Save file to knowledge_base directory
    dest = KNOWLEDGE_BASE_DIR / file.filename
    try:
        contents = await file.read()
        with open(dest, "wb") as f:
            f.write(contents)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")

    # Extract text and ingest
    try:
        text = extract_text(dest)
        if not text.strip():
            dest.unlink(missing_ok=True)
            raise HTTPException(status_code=422, detail="Could not extract any text from the uploaded file.")

        add_document_to_kb(file.filename, text, chunk_size, chunk_overlap)
        
        # Git Sync
        git_success, git_err = sync_git_knowledge_base("add", file.filename)
        warning = "" if git_success else f" (Warning: GitHub sync failed - {git_err})"
        
        return {
            "success": True,
            "message": f"'{file.filename}' ingested successfully.{warning}",
            "chunks": len(text) // chunk_size + 1
        }
    except HTTPException:
        raise
    except Exception as e:
        dest.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api/library/admin/knowledge-base/file/{filename}")
def admin_delete_kb_file(filename: str, admin: User = Depends(get_current_admin_user)):
    """Delete a specific document from the knowledge base by filename."""
    success = delete_document(filename)
    if not success:
        raise HTTPException(status_code=404, detail=f"File '{filename}' not found in knowledge base.")
        
    # Git Sync
    git_success, git_err = sync_git_knowledge_base("rm", filename)
    warning = "" if git_success else f" (Warning: GitHub sync failed - {git_err})"
    
    return {"success": True, "message": f"'{filename}' removed from knowledge base.{warning}"}


@router.delete("/api/library/admin/knowledge-base")
def admin_clear_kb(admin: User = Depends(get_current_admin_user)):
    """Clear all documents from the knowledge base ChromaDB collection."""
    try:
        clear_knowledge_base()
        return {"success": True, "message": "Knowledge base cleared."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/library/admin/knowledge-base/reingest")
def admin_reingest_kb(payload: ReingestPayload, admin: User = Depends(get_current_admin_user)):
    """Clear and rebuild the entire knowledge base from source files using new chunk settings."""
    try:
        clear_knowledge_base()
        ingest_documents(chunk_size=payload.chunk_size, chunk_overlap=payload.chunk_overlap)
        return {"success": True, "message": "Knowledge base rebuilt successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

