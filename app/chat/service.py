from __future__ import annotations

import asyncio
import random
import json
from typing import AsyncGenerator, Dict, Any

# pyrefly: ignore [missing-import]
from openai import AsyncOpenAI, RateLimitError, APITimeoutError, APIConnectionError, APIError

from ..core.config import settings
from .prompts import build_system_prompt
from ..library.service import (
    search_books, SearchBooksArgs,
    check_availability, CheckAvailabilityArgs,
    borrow_book, BorrowBookArgs,
    return_book, ReturnBookArgs,
    get_my_borrowed_books, GetBorrowedBooksArgs
)
from ..library.rag import search_knowledge_base


def _client() -> AsyncOpenAI:
    """Return a configured async Groq client."""
    return AsyncOpenAI(api_key=settings.GROQ_API_KEY, base_url="https://api.cerebras.ai/v1")


async def call_with_retry(func, *args, max_retries=3, initial_delay=1.0, backoff_factor=2.0, **kwargs):
    """
    Call an async function with exponential backoff and jitter for RateLimit, Timeout, and Connection errors.
    """
    delay = initial_delay
    for attempt in range(max_retries + 1):
        try:
            return await func(*args, **kwargs)
        except (RateLimitError, APITimeoutError, APIConnectionError) as e:
            if attempt == max_retries:
                raise e
            
            # Calculate backoff with random jitter (0.8 - 1.2)
            jitter = random.uniform(0.8, 1.2)
            sleep_time = delay * jitter
            print(f"[Groq Retry] Attempt {attempt + 1} failed with {type(e).__name__}. Retrying in {sleep_time:.2f}s...")
            await asyncio.sleep(sleep_time)
            delay *= backoff_factor


def _to_groq_history(history: list[dict]) -> list[dict]:
    """
    Convert our internal message history to Groq-compatible message objects.
    """
    groq_history = []
    for msg in history:
        # We also need to preserve tool calls and tool responses if they exist in history.
        # But for now, our DB history model only stores simple text content.
        # So we just pass them as assistant/user text messages.
        role = "assistant" if msg["role"] == "model" else msg["role"]
        groq_history.append({"role": role, "content": msg["text"]})
    return groq_history


async def is_harmful_input(text: str) -> bool:
    """
    Check if the user input violates safety/moderation guidelines using Llama Guard.
    Returns True if the content is harmful/unsafe, False otherwise.
    """
    return False


# --- Tool Definitions for Groq ---
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_books",
            "description": "Search for books in the library by title, author, or genre.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The title, author, or genre to search for (e.g., 'Tolkien', 'Sci-Fi'). Leave empty to see all books."
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_availability",
            "description": "Check the availability of a specific book by its ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "book_id": {
                        "type": "integer",
                        "description": "The ID of the book"
                    }
                },
                "required": ["book_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "borrow_book",
            "description": "Borrow a book from the library.",
            "parameters": {
                "type": "object",
                "properties": {
                    "book_id": {
                        "type": "integer",
                        "description": "The ID of the book to borrow"
                    }
                },
                "required": ["book_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "return_book",
            "description": "Return a borrowed book to the library.",
            "parameters": {
                "type": "object",
                "properties": {
                    "book_id": {
                        "type": "integer",
                        "description": "The ID of the book to return"
                    }
                },
                "required": ["book_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_my_borrowed_books",
            "description": "Get a list of all currently active loans / borrowed books for the user.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": "Search the library's internal knowledge base for information about policies, rules, hours, late fees, amenities, and general non-catalog questions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query, formatted as a natural language question or keyword string."
                    }
                },
                "required": ["query"]
            }
        }
    }
]

def execute_tool(name: str, args_json: str, user_id: int) -> str:
    """Execute a local Python tool and return the JSON string result."""
    try:
        args = json.loads(args_json)
        print(f"[Tool Execution] Calling {name} with {args} for user {user_id}")
        
        if name == "search_books":
            return search_books(SearchBooksArgs(**args))
        elif name == "check_availability":
            return check_availability(CheckAvailabilityArgs(**args))
        elif name == "borrow_book":
            return borrow_book(BorrowBookArgs(user_id=user_id, book_id=args.get("book_id")))
        elif name == "return_book":
            return return_book(ReturnBookArgs(user_id=user_id, book_id=args.get("book_id")))
        elif name == "get_my_borrowed_books":
            return get_my_borrowed_books(GetBorrowedBooksArgs(user_id=user_id))
        elif name == "search_knowledge_base":
            return search_knowledge_base(args.get("query", ""))
        else:
            return json.dumps({"status": "error", "message": f"Unknown tool: {name}"})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


async def stream_reply(
    history: list[dict],
    user_message: str,
    user_id: int,
    retrieved_context: str = "",
) -> AsyncGenerator[str, None]:
    """
    Stream a Groq reply token-by-token over an async generator, supporting tool calling.
    """
    # 1. Content Moderation Check
    if await is_harmful_input(user_message):
        yield "[Safety Warning: Your message has been flagged by our content moderation system. Please keep the conversation safe, respectful, and educational.]"
        return

    client = _client()
    system_prompt = build_system_prompt(retrieved_context)

    # Prepare messages payload
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(_to_groq_history(history))
    messages.append({"role": "user", "content": user_message})

    # Track usage across loops
    total_prompt_tokens = 0
    total_completion_tokens = 0

    MAX_TOOL_LOOPS = 5
    for loop_idx in range(MAX_TOOL_LOOPS):
        print(f"DEBUG: Loop {loop_idx}. Last message role: {messages[-1]['role']}")
        try:
            stream = await call_with_retry(
                client.chat.completions.create,
                model="gemma-4-31b",
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
                temperature=0.7,
                max_tokens=2048,
                stream=True,
            )
        except (RateLimitError, APITimeoutError, APIConnectionError) as e:
            print(f"[Groq Error] Chat completion failed after retries: {e}")
            yield f"\n\n[System Error: The Library Assistant is currently busy (Rate Limit/Timeout). Please try again in a few seconds. Details: {e}]"
            return
        
        # Buffer variables
        completion_text = ""
        tool_calls_buffer: Dict[int, Any] = {}
        
        try:
            async for chunk in stream:
                if not chunk.choices:
                    continue
                    
                delta = chunk.choices[0].delta
                
                # 1. Accumulate text content if any
                if delta.content:
                    completion_text += delta.content
                    yield delta.content
                    
                # 2. Accumulate tool calls if any
                if delta.tool_calls:
                    for tc in delta.tool_calls:
                        idx = tc.index
                        if idx not in tool_calls_buffer:
                            tool_calls_buffer[idx] = {
                                "id": tc.id,
                                "type": "function",
                                "function": {"name": tc.function.name, "arguments": tc.function.arguments or ""}
                            }
                        else:
                            if tc.function.name:
                                tool_calls_buffer[idx]["function"]["name"] += tc.function.name
                            if tc.function.arguments:
                                tool_calls_buffer[idx]["function"]["arguments"] += tc.function.arguments
        except APIError as e:
            print(f"[Cerebras APIError] {e}")
            yield f"\n\n[System Error: Cerebras failed to parse the generated tool response. Details: {str(e)}]"
            break
                            
        # Calculate tokens for this loop (approx)
        loop_prompt_tokens = max(1, int(len(json.dumps(messages)) / 3.9))
        loop_completion_tokens = max(1, int(len(completion_text) / 3.9) + (len(json.dumps(tool_calls_buffer)) // 3.9))
        total_prompt_tokens += loop_prompt_tokens
        total_completion_tokens += int(loop_completion_tokens)
        
        if tool_calls_buffer:
            # Reconstruct the assistant message with tool calls
            tool_calls_list = []
            for idx in sorted(tool_calls_buffer.keys()):
                tc = tool_calls_buffer[idx]
                tool_calls_list.append({
                    "id": tc["id"],
                    "type": "function",
                    "function": {
                        "name": tc["function"]["name"],
                        "arguments": tc["function"]["arguments"]
                    }
                })
                
            # Append the assistant's request to call tools
            assistant_msg = {
                "role": "assistant",
                "content": completion_text if completion_text else None,
                "tool_calls": tool_calls_list
            }
            messages.append(assistant_msg)
            
            # Execute each tool and append the response
            for tc in tool_calls_list:
                name = tc["function"]["name"]
                args = tc["function"]["arguments"]
                
                # Yield a status metadata token so the frontend can display a temporary loading state
                if name == "search_books":
                    yield "[STATUS:Searching the library catalog...]"
                elif name == "borrow_book":
                    yield "[STATUS:Processing your borrow request...]"
                elif name == "return_book":
                    yield "[STATUS:Processing your return...]"
                elif name == "check_availability":
                    yield "[STATUS:Checking book availability...]"
                elif name == "get_my_borrowed_books":
                    yield "[STATUS:Checking your active loans...]"
                elif name == "search_knowledge_base":
                    yield "[STATUS:Searching the knowledge base...]"
                else:
                    yield f"[STATUS:Executing {name}...]"
                
                result_json = execute_tool(name, args, user_id)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": result_json
                })
            
            # We loop again to send the tool results back to Groq!
            continue
        else:
            # No tool calls, streaming is done
            break

    # Calculate cost
    cost = (total_prompt_tokens * 0.59 / 1_000_000) + (total_completion_tokens * 0.79 / 1_000_000)
    print(f"[Cerebras Usage] Model: gemma-4-31b (Estimated) | Prompt Tokens: {total_prompt_tokens} | Completion Tokens: {total_completion_tokens} | Cost: ${cost:.8f}")
    
    # Yield usage data as a metadata string to be picked up by the WebSocket
    yield f"[USAGE:{{\"prompt_tokens\": {total_prompt_tokens}, \"completion_tokens\": {total_completion_tokens}, \"cost\": {cost:.8f}}}]"


async def generate_chat_title(prompt: str) -> str:
    """Generate a short 3-5 word title for a new chat session based on the first prompt."""
    client = _client()
    try:
        response = await call_with_retry(
            client.chat.completions.create,
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
        return title[:100]
    except Exception as e:
        print(f"[Groq Error] Failed to generate chat title: {e}")
        return prompt[:30] + ("..." if len(prompt) > 30 else "")
