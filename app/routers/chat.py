from __future__ import annotations

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.deps import get_current_user_ws


router = APIRouter()


def build_bot_reply(message: str) -> str:
    text = message.strip()
    lower_text = text.lower()

    if not text:
        return "AI bot: say something and I will reply."
    if any(word in lower_text for word in ("hello", "hi", "hey")):
        return "AI bot: hello. How can I help you today?"
    if "name" in lower_text:
        return "AI bot: I am your simple FastAPI demo bot."
    if lower_text.endswith("?"):
        return "AI bot: that is a good question. I am still a simple demo bot."
    return f"AI bot: you said '{text}'"


@router.websocket("/ws/chat")
async def chat_socket(
    websocket: WebSocket,
    token: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """Authenticated WebSocket chat endpoint.

    Clients must pass a valid JWT as the ``?token=`` query parameter.
    Unauthorized connections are rejected with close code 1008 (Policy Violation).
    """
    user = get_current_user_ws(token, db)
    if user is None:
        await websocket.close(code=1008)
        return

    await websocket.accept()
    await websocket.send_text(f"AI bot: connected. Hello {user.username}! Send me a message.")

    try:
        while True:
            message = await websocket.receive_text()
            await websocket.send_text(build_bot_reply(message))
    except WebSocketDisconnect:
        return