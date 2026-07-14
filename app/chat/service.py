from __future__ import annotations

from typing import AsyncGenerator

from google import genai
from google.genai import types

from ..core.config import settings
from .prompts import build_system_prompt


def _client() -> genai.Client:
    """Return a configured Gemini client."""
    return genai.Client(api_key=settings.GEMINI_API_KEY)


def _to_gemini_history(history: list[dict]) -> list[types.Content]:
    """
    Convert our internal message history to Gemini Content objects.

    Each item in `history` is expected to be:
        {"role": "user" | "model", "text": "..."}
    """
    return [
        types.Content(
            role=msg["role"],
            parts=[types.Part(text=msg["text"])],
        )
        for msg in history
    ]


async def stream_reply(
    history: list[dict],
    user_message: str,
    retrieved_context: str = "",
) -> AsyncGenerator[str, None]:
    """
    Stream a Gemini reply token-by-token over an async generator.

    Args:
        history:           List of previous turns [{role, text}, ...].
                           Role must be "user" or "model".
        user_message:      The latest message from the user.
        retrieved_context: Optional RAG chunks to inject into the system prompt.

    Yields:
        Text chunks as they arrive from the model.
    """
    client = _client()
    system_prompt = build_system_prompt(retrieved_context)

    # Append the new user turn to the history for the API call
    contents = _to_gemini_history(history) + [
        types.Content(
            role="user",
            parts=[types.Part(text=user_message)],
        )
    ]

    response_stream = await client.aio.models.generate_content_stream(
        model="gemini-2.0-flash",
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.7,
            max_output_tokens=2048,
        ),
    )
    async for chunk in response_stream:
        if chunk.text:
            yield chunk.text
