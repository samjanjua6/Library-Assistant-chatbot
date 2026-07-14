from __future__ import annotations

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.deps import get_current_user_ws
from .service import stream_reply


router = APIRouter(tags=["Chat"])


@router.websocket("/ws/chat")
async def chat_socket(
    websocket: WebSocket,
    token: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """Authenticated WebSocket chat endpoint powered by Gemini AI.

    Clients must pass a valid JWT as the ``?token=`` query parameter.
    Unauthorized connections are rejected with close code 1008 (Policy Violation).

    Protocol:
        → client sends a plain-text message
        ← server streams back the AI reply in chunks (token by token)
        ← server sends the special sentinel "[DONE]" when the reply is complete
    """
    user = get_current_user_ws(token, db)
    if user is None:
        await websocket.close(code=1008)
        return

    await websocket.accept()
    await websocket.send_text(
        f"Aao **{user.username}**, baitho. Hum Munna Bhaiya hain, Mirzapur ke agle king. Bol, kya bawal laaye ho aaj?"
    )

    # In-memory conversation history for this WebSocket session.
    # Each turn: {"role": "user" | "model", "text": "..."}
    history: list[dict] = []

    try:
        while True:
            user_message = await websocket.receive_text()

            if not user_message.strip():
                continue

            # ── RAG hook ──────────────────────────────────────────────────────
            # To enable RAG, retrieve relevant chunks here and pass them as
            # `retrieved_context` to stream_reply().
            #
            # Example (plug in your own retriever):
            #   chunks = await retriever.query(user_message, top_k=5)
            #   retrieved_context = "\n\n".join(c.text for c in chunks)
            #
            retrieved_context = ""   # ← replace with your retriever call
            # ─────────────────────────────────────────────────────────────────

            # Stream the Gemini reply token-by-token
            full_reply = ""
            try:
                async for token_chunk in stream_reply(history, user_message, retrieved_context):
                    full_reply += token_chunk
                    await websocket.send_text(token_chunk)
            except Exception as e:
                err_msg = f"\n\n[System Error: Failed to generate response from Gemini. It might be a quota limit (429) or invalid API key. Details: {str(e)}]"
                full_reply += err_msg
                await websocket.send_text(err_msg)

            # Signal to the client that streaming is complete
            await websocket.send_text("[DONE]")

            # Update conversation history
            history.append({"role": "user",  "text": user_message})
            history.append({"role": "model", "text": full_reply})

    except WebSocketDisconnect:
        return
