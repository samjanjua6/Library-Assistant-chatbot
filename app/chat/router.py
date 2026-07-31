from __future__ import annotations

# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect, UploadFile, File, HTTPException
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session
# pyrefly: ignore [missing-import]
from sqlalchemy import select

from ..core.database import get_db
from ..core.deps import get_current_user_ws, get_current_user
from ..users.model import User
from .model import ChatSession, ChatMessage, SessionDocument
from .service import stream_reply, generate_chat_title
from .upload import validate_upload, save_upload
from ..library.rag import SESSION_UPLOADS_DIR


router = APIRouter(tags=["Chat"])


@router.get("/api/chat/sessions")
def get_sessions(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get all chat sessions for the current user."""
    sessions = db.scalars(
        select(ChatSession)
        .where(ChatSession.user_id == user.id)
        .order_by(ChatSession.created_at.desc())
    ).all()
    return [{"id": s.id, "title": s.title, "created_at": s.created_at} for s in sessions]


@router.post("/api/chat/sessions")
def create_session(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create a new chat session."""
    session = ChatSession(user_id=user.id, title="New Chat")
    db.add(session)
    db.commit()
    db.refresh(session)
    return {"id": session.id, "title": session.title, "created_at": session.created_at}


@router.get("/api/chat/sessions/{session_id}/messages")
def get_session_messages(
    session_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get historical messages for a session."""
    # Verify ownership
    session = db.scalar(select(ChatSession).where(ChatSession.id == session_id, ChatSession.user_id == user.id))
    if not session:
        return []
    
    messages = db.scalars(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
    ).all()
    return [{"id": m.id, "role": m.role, "content": m.content, "created_at": m.created_at} for m in messages]


@router.delete("/api/chat/sessions/{session_id}")
def delete_session(
    session_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Delete a chat session."""
    session = db.scalar(select(ChatSession).where(ChatSession.id == session_id, ChatSession.user_id == user.id))
    if not session:
        return {"success": False, "error": "Session not found or unauthorized"}
    
    # Delete all messages associated with the session first to avoid foreign key constraint errors
    db.query(ChatMessage).filter(ChatMessage.session_id == session.id).delete()
    db.delete(session)
    db.commit()
    return {"success": True}


# ── Session Document Endpoints ────────────────────────────────────────────────

@router.post("/api/chat/sessions/{session_id}/upload")
async def upload_session_document(
    session_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Upload a document into a chat session.

    Validates ownership, MIME type (via libmagic sniffing), and size (≤ 20 MB).
    Saves the file to disk and enqueues an ARQ background job to extract, chunk,
    and index it into ChromaDB with full session/user scoping.

    Returns the new ``document_id`` and ``status='pending'``.
    """
    # Verify session ownership
    session = db.scalar(
        select(ChatSession).where(ChatSession.id == session_id, ChatSession.user_id == user.id)
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    # Read file bytes
    data = await file.read()

    # Validate (size + extension + MIME sniff)
    ok, err_msg, safe_filename = validate_upload(file.filename or "upload", data)
    if not ok:
        raise HTTPException(status_code=400, detail=err_msg)

    # Save file to disk
    file_path = save_upload(
        data=data,
        safe_filename=safe_filename,
        user_id=user.id,
        session_id=session_id,
        base_dir=SESSION_UPLOADS_DIR,
    )

    # Create DB record
    doc = SessionDocument(
        session_id=session_id,
        user_id=user.id,
        original_filename=file.filename or safe_filename,
        stored_filename=safe_filename,
        file_size_bytes=len(data),
        mime_type=file.content_type or "",
        status="pending",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # Enqueue ARQ background job
    try:
        from arq import create_pool  # pyrefly: ignore [missing-import]
        # pyrefly: ignore [missing-import]
        from arq.connections import RedisSettings
        from ..core.config import settings as app_settings

        url = app_settings.REDIS_URL.replace("redis://", "").replace("rediss://", "")
        host_port, *db_parts = url.split("/")
        db_num = int(db_parts[0]) if db_parts else 0
        host, port = (host_port.split(":", 1) if ":" in host_port else (host_port, "6379"))

        redis_pool = await create_pool(RedisSettings(host=host, port=int(port), database=db_num))
        await redis_pool.enqueue_job(
            "process_session_document",
            document_id=doc.id,
            file_path=str(file_path),
            session_id=session_id,
            user_id=user.id,
            filename=safe_filename,
        )
        await redis_pool.close()
    except Exception as e:
        # If Redis is down, fall back to synchronous in-process ingestion
        import logging
        logging.getLogger(__name__).warning(
            f"[Upload] Redis unavailable ({e}), processing synchronously."
        )
        try:
            from ..library.rag import ingest_session_document
            from datetime import datetime, timezone
            chunk_count = ingest_session_document(
                document_id=doc.id,
                session_id=session_id,
                user_id=user.id,
                filename=safe_filename,
                file_path=file_path,
            )
            doc.status = "ready"
            doc.chunk_count = chunk_count
            doc.updated_at = datetime.now(timezone.utc)
            db.commit()
        except Exception as ingest_err:
            from datetime import datetime, timezone
            doc.status = "failed"
            doc.error_message = str(ingest_err)[:2000]
            doc.updated_at = datetime.now(timezone.utc)
            db.commit()

    return {
        "document_id": doc.id,
        "original_filename": doc.original_filename,
        "status": doc.status,
        "file_size_bytes": doc.file_size_bytes,
    }


@router.get("/api/chat/sessions/{session_id}/documents")
def list_session_documents(
    session_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List all documents attached to a chat session (ownership enforced)."""
    # Verify session ownership
    session = db.scalar(
        select(ChatSession).where(ChatSession.id == session_id, ChatSession.user_id == user.id)
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    docs = db.scalars(
        select(SessionDocument)
        .where(SessionDocument.session_id == session_id, SessionDocument.user_id == user.id)
        .order_by(SessionDocument.created_at.desc())
    ).all()

    return [
        {
            "document_id": d.id,
            "original_filename": d.original_filename,
            "file_size_bytes": d.file_size_bytes,
            "status": d.status,
            "chunk_count": d.chunk_count,
            "error_message": d.error_message,
            "created_at": d.created_at,
        }
        for d in docs
    ]


@router.get("/api/chat/sessions/{session_id}/documents/{doc_id}/status")
def get_document_status(
    session_id: int,
    doc_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Poll the processing status of an uploaded document."""
    doc = db.scalar(
        select(SessionDocument).where(
            SessionDocument.id == doc_id,
            SessionDocument.session_id == session_id,
            SessionDocument.user_id == user.id,
        )
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    return {
        "document_id": doc.id,
        "original_filename": doc.original_filename,
        "status": doc.status,
        "chunk_count": doc.chunk_count,
        "error_message": doc.error_message,
    }


@router.delete("/api/chat/sessions/{session_id}/documents/{doc_id}")
def delete_session_document(
    session_id: int,
    doc_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Delete an uploaded document and its ChromaDB chunks."""
    doc = db.scalar(
        select(SessionDocument).where(
            SessionDocument.id == doc_id,
            SessionDocument.session_id == session_id,
            SessionDocument.user_id == user.id,
        )
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    # Remove chunks from ChromaDB
    from ..library.rag import delete_session_document_chunks
    delete_session_document_chunks(doc_id, session_id)

    db.delete(doc)
    db.commit()
    return {"success": True, "message": f"Deleted document '{doc.original_filename}'."}


@router.post("/api/chat/sessions/{session_id}/upload-image")
async def upload_session_image(
    session_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Upload an image for OCR text extraction.
    Returns the extracted text.
    """
    # Verify session ownership
    session = db.scalar(
        select(ChatSession).where(ChatSession.id == session_id, ChatSession.user_id == user.id)
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    # Validate it's an image
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image.")

    # Read file bytes
    data = await file.read()
    
    # Run OCR
    try:
        from ..library.ocr import extract_text_from_image
        extracted_text = extract_text_from_image(data)
        return {"success": True, "text": extracted_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}")


# ── WebSocket Chat ─────────────────────────────────────────────────────────────

@router.websocket("/ws/chat")
async def chat_socket(
    websocket: WebSocket,
    token: str | None = Query(default=None),
    session_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """Authenticated WebSocket chat endpoint powered by Groq AI."""
    user = get_current_user_ws(token, db)
    if user is None:
        await websocket.close(code=1008)
        return

    # Verify session ownership if provided
    chat_session = None
    if session_id:
        chat_session = db.scalar(
            select(ChatSession).where(ChatSession.id == session_id, ChatSession.user_id == user.id)
        )
    
    # Load history from DB if session exists
    history = []
    if chat_session:
        db_messages = db.scalars(
            select(ChatMessage)
            .where(ChatMessage.session_id == chat_session.id)
            .order_by(ChatMessage.created_at.asc())
        ).all()
        history = [{"role": m.role, "text": m.content} for m in db_messages]

    # Discover the active (ready) document for this session, if any
    active_document: SessionDocument | None = None
    if chat_session:
        active_document = db.scalar(
            select(SessionDocument).where(
                SessionDocument.session_id == chat_session.id,
                SessionDocument.user_id == user.id,
                SessionDocument.status == "ready",
            ).order_by(SessionDocument.created_at.desc())
        )

    await websocket.accept()

    # Send welcome message only if it's a completely new chat with no history
    if not history:
        await websocket.send_text(
            f"Hello **{user.username}**! I am your Library Book Assistant. 📚 I am excited to help you search our catalog, check availability, borrow, or return books. How can I help you today?"
        )
        await websocket.send_text("[DONE]")

    # If a document is already ready, notify the frontend immediately
    if active_document:
        import json as _json
        await websocket.send_text(
            f"[DOC_READY:{_json.dumps({'document_id': active_document.id, 'filename': active_document.original_filename, 'chunk_count': active_document.chunk_count})}]"
        )

    try:
        while True:
            user_message = await websocket.receive_text()

            if not user_message.strip():
                continue

            # Handle document status refresh request from frontend
            if user_message.startswith("[CHECK_DOC:") and chat_session:
                import json as _json
                try:
                    doc_id = int(user_message.replace("[CHECK_DOC:", "").replace("]", ""))
                    fresh_doc = db.scalar(
                        select(SessionDocument).where(
                            SessionDocument.id == doc_id,
                            SessionDocument.session_id == chat_session.id,
                            SessionDocument.user_id == user.id,
                        )
                    )
                    db.refresh(fresh_doc) if fresh_doc else None
                    if fresh_doc:
                        await websocket.send_text(
                            f"[DOC_STATUS:{_json.dumps({'document_id': fresh_doc.id, 'status': fresh_doc.status, 'filename': fresh_doc.original_filename, 'chunk_count': fresh_doc.chunk_count})}]"
                        )
                        if fresh_doc.status == "ready":
                            active_document = fresh_doc
                except Exception:
                    pass
                continue

            # If no active session, create one dynamically upon first user prompt
            if not chat_session:
                title = await generate_chat_title(user_message)
                chat_session = ChatSession(user_id=user.id, title=title)
                db.add(chat_session)
                db.commit()
                db.refresh(chat_session)
                # Inform the frontend to update its active session
                await websocket.send_text(f"[SESSION_ID:{chat_session.id}]")
            elif chat_session.title == "New Chat":
                chat_session.title = await generate_chat_title(user_message)
                db.commit()
                db.refresh(chat_session)
                # Send ID again to trigger a sidebar refresh on the frontend
                await websocket.send_text(f"[SESSION_ID:{chat_session.id}]")

            # Save user message
            msg = ChatMessage(session_id=chat_session.id, role="user", content=user_message)
            db.add(msg)
            db.commit()

            retrieved_context = ""   # ← legacy param, kept for compat

            # Refresh the active document from DB on every turn.
            # This covers the sync-fallback path (Redis down) where active_document
            # was never set via a [CHECK_DOC:] frame, and eliminates race conditions
            # where the user sends a message immediately after the document becomes ready.
            if chat_session and not active_document:
                active_document = db.scalar(
                    select(SessionDocument).where(
                        SessionDocument.session_id == chat_session.id,
                        SessionDocument.user_id == user.id,
                        SessionDocument.status == "ready",
                    ).order_by(SessionDocument.created_at.desc())
                )

            # Stream the reply token-by-token
            full_reply = ""
            try:
                active_doc_id = active_document.id if active_document else None
                async for token_chunk in stream_reply(
                    history, user_message, user.id, retrieved_context,
                    active_document_id=active_doc_id,
                    active_session_id=chat_session.id if chat_session else None,
                ):
                    if token_chunk.startswith("[USAGE:") or token_chunk.startswith("[STATUS:") or token_chunk.startswith("[METRICS:") or token_chunk.startswith("[CHUNKS:"):
                        await websocket.send_text(token_chunk)
                        continue
                    full_reply += token_chunk
                    await websocket.send_text(token_chunk)
            except Exception as e:
                err_msg = f"\n\n[System Error: Failed to generate response. Details: {str(e)}]"
                full_reply += err_msg
                await websocket.send_text(err_msg)

            # Signal to the client that streaming is complete
            await websocket.send_text("[DONE]")

            # Save bot message
            bot_msg = ChatMessage(session_id=chat_session.id, role="model", content=full_reply)
            db.add(bot_msg)
            db.commit()

            # Update conversation history
            history.append({"role": "user",  "text": user_message})
            history.append({"role": "model", "text": full_reply})

    except WebSocketDisconnect:
        return
    except Exception as exc:
        import traceback
        with open("/app/data/crash.log", "a") as f:
            f.write(f"CRASH: {exc}\n{traceback.format_exc()}\n")
        raise
