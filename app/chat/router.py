from __future__ import annotations

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from sqlalchemy import select

from ..core.database import get_db
from ..core.deps import get_current_user_ws, get_current_user
from ..users.model import User
from .model import ChatSession, ChatMessage
from .service import stream_reply, generate_chat_title


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

    await websocket.accept()

    # Send welcome message only if it's a completely new chat with no history
    if not history:
        await websocket.send_text(
            f"Aao **{user.username}**, baitho. Hum Munna Bhaiya hain, Mirzapur ke agle king. Bol, kya bawal laaye ho aaj?"
        )
        await websocket.send_text("[DONE]")

    try:
        while True:
            user_message = await websocket.receive_text()

            if not user_message.strip():
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

            retrieved_context = ""   # ← replace with your retriever call

            # Stream the Groq reply token-by-token
            full_reply = ""
            try:
                async for token_chunk in stream_reply(history, user_message, retrieved_context):
                    full_reply += token_chunk
                    await websocket.send_text(token_chunk)
            except Exception as e:
                err_msg = f"\n\n[System Error: Failed to generate response from Groq. It might be a quota limit or invalid API key. Details: {str(e)}]"
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
