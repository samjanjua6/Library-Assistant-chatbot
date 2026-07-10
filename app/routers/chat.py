from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect


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
async def chat_socket(websocket: WebSocket):
	await websocket.accept()
	await websocket.send_text("AI bot: connected. Send me a message.")

	try:
		while True:
			message = await websocket.receive_text()
			await websocket.send_text(build_bot_reply(message))
	except WebSocketDisconnect:
		return