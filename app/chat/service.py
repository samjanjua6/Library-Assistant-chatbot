from __future__ import annotations

from typing import AsyncGenerator

from groq import AsyncGroq

from ..core.config import settings
from .prompts import build_system_prompt


def _client() -> AsyncGroq:
    """Return a configured async Groq client."""
    return AsyncGroq(api_key=settings.GROQ_API_KEY)


def _to_groq_history(history: list[dict]) -> list[dict]:
    """
    Convert our internal message history to Groq-compatible message objects.

    Each item in `history` is expected to be:
        {"role": "user" | "model", "text": "..."}
        
    Groq expects "assistant" instead of "model" and "content" instead of "text".
    """
    groq_history = []
    for msg in history:
        role = "assistant" if msg["role"] == "model" else msg["role"]
        groq_history.append({"role": role, "content": msg["text"]})
    return groq_history


async def stream_reply(
    history: list[dict],
    user_message: str,
    retrieved_context: str = "",
) -> AsyncGenerator[str, None]:
    """
    Stream a Groq reply token-by-token over an async generator.

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

    # Prepare messages payload
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(_to_groq_history(history))
    messages.append({"role": "user", "content": user_message})

    # Call the Groq API with streaming enabled
    stream = await client.chat.completions.create(
        model="llama-3.3-70b-versatile",  # Defaulting to a fast, reliable Groq model
        messages=messages,
        temperature=0.7,
        max_tokens=2048,
        stream=True,
    )
    
    async for chunk in stream:
        content = chunk.choices[0].delta.content
        if content:
            yield content

async def generate_chat_title(prompt: str) -> str:
    """Generate a short 3-5 word title for a new chat session based on the first prompt."""
    client = _client()
    try:
        response = await client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that generates extremely short titles (2-5 words max) for a conversation based on the user's first message. Do NOT use quotes around the title. Do NOT add any preamble. Just output the short title."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=15,
            stream=False,
        )
        title = response.choices[0].message.content.strip().strip('"').strip("'")
        return title[:100]  # Ensure it fits in the DB column
    except Exception:
        # Fallback if title generation fails
        return prompt[:30] + ("..." if len(prompt) > 30 else "")
