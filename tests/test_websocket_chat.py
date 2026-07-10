from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_websocket_chat_replies_like_a_simple_bot():
    client = TestClient(app)

    with client.websocket_connect("/ws/chat") as websocket:
        assert websocket.receive_text() == "AI bot: connected. Send me a message."

        websocket.send_text("hello")
        assert websocket.receive_text() == "AI bot: hello. How can I help you today?"

        websocket.send_text("What can you do?")
        assert websocket.receive_text() == "AI bot: that is a good question. I am still a simple demo bot."