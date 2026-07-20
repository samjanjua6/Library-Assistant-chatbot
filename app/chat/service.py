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
from ..library.evaluator import evaluate_retrieval


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


# --- Tool Definitions ---
ORCHESTRATOR_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "call_catalog_agent",
            "description": "Route to the Library Catalog Specialist to handle finding books, checking availability, borrowing, returning, and listing active loans.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The explicit request to pass to the Catalog Agent."
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "call_policy_agent",
            "description": "Route to the Policy Specialist to search the knowledge base for library rules, fees, hours, and amenities.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The explicit question to pass to the Policy Agent."
                    }
                },
                "required": ["query"]
            }
        }
    }
]

CATALOG_TOOLS = [
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
                        "description": "The title, author, or genre to search for. Leave empty to see all books."
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
                    "book_id": {"type": "integer"}
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
                    "book_id": {"type": "integer"}
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
                    "book_id": {"type": "integer"}
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
    }
]

POLICY_TOOLS = [
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


async def run_catalog_agent(query: str, user_id: int) -> tuple[str, int, int]:
    """Agent specialized in catalog operations. Returns (response_text, prompt_tokens, completion_tokens)."""
    client = _client()
    messages = [
        {"role": "system", "content": "You are the Library Catalog Agent. Use your tools to search books, check availability, borrow, return, and list active loans to fulfill the user's request. Answer concisely."},
        {"role": "user", "content": query}
    ]
    p_tokens, c_tokens = 0, 0
    for _ in range(3):
        try:
            resp = await call_with_retry(
                client.chat.completions.create,
                model="gemma-4-31b",
                messages=messages,
                tools=CATALOG_TOOLS,
                tool_choice="auto",
                temperature=0.3,
                max_tokens=1024,
            )
            msg = resp.choices[0].message
            p_tokens += resp.usage.prompt_tokens if resp.usage else 0
            c_tokens += resp.usage.completion_tokens if resp.usage else 0
            
            if msg.tool_calls:
                messages.append(msg)
                for tc in msg.tool_calls:
                    res = execute_tool(tc.function.name, tc.function.arguments, user_id)
                    messages.append({"role": "tool", "tool_call_id": tc.id, "content": res})
            else:
                return msg.content or "Task complete.", p_tokens, c_tokens
        except Exception as e:
            return f"Catalog Agent Error: {e}", p_tokens, c_tokens
    return "Catalog Agent max loops reached.", p_tokens, c_tokens


async def run_policy_agent(query: str, user_id: int) -> tuple[str, list, int, int]:
    """Agent specialized in policy/knowledge base. Returns (response_text, retrieved_chunks, prompt_tokens, completion_tokens)."""
    client = _client()
    messages = [
        {"role": "system", "content": "You are the Policy Agent. Use your search_knowledge_base tool to answer the user's questions about library rules, fees, hours, etc. Answer concisely based only on retrieved context."},
        {"role": "user", "content": query}
    ]
    p_tokens, c_tokens = 0, 0
    kb_chunks = []
    for _ in range(3):
        try:
            resp = await call_with_retry(
                client.chat.completions.create,
                model="gemma-4-31b",
                messages=messages,
                tools=POLICY_TOOLS,
                tool_choice="auto",
                temperature=0.3,
                max_tokens=1024,
            )
            msg = resp.choices[0].message
            p_tokens += resp.usage.prompt_tokens if resp.usage else 0
            c_tokens += resp.usage.completion_tokens if resp.usage else 0
            
            if msg.tool_calls:
                messages.append(msg)
                for tc in msg.tool_calls:
                    res = execute_tool(tc.function.name, tc.function.arguments, user_id)
                    if tc.function.name == "search_knowledge_base":
                        try:
                            parsed = json.loads(res)
                            if parsed.get("status") == "success":
                                kb_chunks.extend(parsed.get("results", []))
                        except Exception:
                            pass
                    messages.append({"role": "tool", "tool_call_id": tc.id, "content": res})
            else:
                return msg.content or "Task complete.", kb_chunks, p_tokens, c_tokens
        except Exception as e:
            return f"Policy Agent Error: {e}", kb_chunks, p_tokens, c_tokens
    return "Policy Agent max loops reached.", kb_chunks, p_tokens, c_tokens


async def stream_reply(
    history: list[dict],
    user_message: str,
    user_id: int,
    retrieved_context: str = "",
) -> AsyncGenerator[str, None]:
    """
    Orchestrator stream_reply. Acts as a router.
    """
    if await is_harmful_input(user_message):
        yield "[Safety Warning: Content flagged.]"
        return

    client = _client()
    orchestrator_prompt = "You are the Orchestrator for the Library Assistant. Your job is routing, not answering. Delegate catalog queries to the Catalog Agent. Delegate policy/rules queries to the Policy Agent. If the user's message is a simple greeting, you can reply directly. DO NOT attempt to answer policy or catalog questions yourself. Use your routing tools."
    
    messages = [{"role": "system", "content": orchestrator_prompt}]
    messages.extend(_to_groq_history(history))
    messages.append({"role": "user", "content": user_message})

    total_prompt_tokens = 0
    total_completion_tokens = 0
    kb_eval_data = {"question": user_message, "chunks": [], "error": None}

    MAX_ROUTING_HOPS = 3
    for loop_idx in range(MAX_ROUTING_HOPS):
        try:
            stream = await call_with_retry(
                client.chat.completions.create,
                model="gemma-4-31b",
                messages=messages,
                tools=ORCHESTRATOR_TOOLS,
                tool_choice="auto",
                temperature=0.3,
                max_tokens=2048,
                stream=True,
            )
        except Exception as e:
            yield f"\n\n[System Error: Orchestrator failed: {e}]"
            return
        
        completion_text = ""
        tool_calls_buffer = {}
        
        try:
            async for chunk in stream:
                if not chunk.choices: continue
                delta = chunk.choices[0].delta
                
                if delta.content:
                    completion_text += delta.content
                    yield delta.content
                    
                if delta.tool_calls:
                    for tc in delta.tool_calls:
                        idx = tc.index
                        if idx not in tool_calls_buffer:
                            tool_calls_buffer[idx] = {"id": tc.id, "type": "function", "function": {"name": tc.function.name, "arguments": tc.function.arguments or ""}}
                        else:
                            if tc.function.name: tool_calls_buffer[idx]["function"]["name"] += tc.function.name
                            if tc.function.arguments: tool_calls_buffer[idx]["function"]["arguments"] += tc.function.arguments
        except Exception as e:
            yield f"\n\n[System Error: Stream failed: {e}]"
            break
            
        loop_p = max(1, int(len(json.dumps(messages)) / 3.9))
        loop_c = max(1, int(len(completion_text) / 3.9) + (len(json.dumps(tool_calls_buffer)) // 3.9))
        total_prompt_tokens += loop_p
        total_completion_tokens += loop_c
        
        if tool_calls_buffer:
            tool_calls_list = []
            for idx in sorted(tool_calls_buffer.keys()):
                tc = tool_calls_buffer[idx]
                tool_calls_list.append({"id": tc["id"], "type": "function", "function": {"name": tc["function"]["name"], "arguments": tc["function"]["arguments"]}})
                
            messages.append({"role": "assistant", "content": completion_text if completion_text else None, "tool_calls": tool_calls_list})
            
            for tc in tool_calls_list:
                name = tc["function"]["name"]
                try:
                    args = json.loads(tc["function"]["arguments"])
                except Exception:
                    args = {}
                query = args.get("query", user_message)
                
                if name == "call_catalog_agent":
                    yield "\n\n*[STATUS: Delegating to Catalog Agent...]*\n"
                    res_text, p_tok, c_tok = await run_catalog_agent(query, user_id)
                    total_prompt_tokens += p_tok
                    total_completion_tokens += c_tok
                    messages.append({"role": "tool", "tool_call_id": tc["id"], "content": res_text})
                    
                elif name == "call_policy_agent":
                    yield "\n\n*[STATUS: Delegating to Policy Agent...]*\n"
                    res_text, chunks, p_tok, c_tok = await run_policy_agent(query, user_id)
                    kb_eval_data["chunks"].extend(chunks)
                    total_prompt_tokens += p_tok
                    total_completion_tokens += c_tok
                    messages.append({"role": "tool", "tool_call_id": tc["id"], "content": res_text})
                else:
                    messages.append({"role": "tool", "tool_call_id": tc["id"], "content": f"Unknown agent: {name}"})
            continue
        else:
            break
    else:
        yield "\n\n[System Warning: Max routing hops reached. Orchestrator forced to stop.]"

    cost = (total_prompt_tokens * 0.59 / 1_000_000) + (total_completion_tokens * 0.79 / 1_000_000)
    print(f"[Cerebras Usage] Model: gemma-4-31b (Estimated) | Prompt Tokens: {total_prompt_tokens} | Completion Tokens: {total_completion_tokens} | Cost: ${cost:.8f}")

    # ── Precision / Recall Evaluation ─────────────────────────────────────────
    metrics = await evaluate_retrieval(kb_eval_data["question"], kb_eval_data["chunks"])
    yield f"[METRICS:{json.dumps(metrics)}]"
    # ──────────────────────────────────────────────────────────────────────────

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
