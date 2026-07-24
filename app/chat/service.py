from __future__ import annotations

import json
from typing import AsyncGenerator

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import tool

from ..core.config import settings
from .prompts import build_system_prompt
from ..library.service import (
    search_books, check_availability, borrow_book, return_book, get_my_borrowed_books
)
from ..library.rag import search_knowledge_base
from ..library.evaluator import evaluate_retrieval

def _client(model_name: str = "gemma-4-31b") -> ChatOpenAI:
    """Return a configured async LangChain OpenAI client pointing to Cerebras."""
    return ChatOpenAI(
        api_key=settings.GROQ_API_KEY, 
        base_url="https://api.cerebras.ai/v1", 
        model=model_name,
        temperature=0.3,
        max_retries=3
    )

def _to_langchain_history(history: list[dict]) -> list:
    """Convert our internal message history to LangChain message objects."""
    lc_history = []
    for msg in history:
        if msg["role"] == "model":
            lc_history.append(AIMessage(content=msg["text"]))
        else:
            lc_history.append(HumanMessage(content=msg["text"]))
    return lc_history

async def is_harmful_input(text: str) -> bool:
    """Check if the user input violates safety/moderation guidelines."""
    return False

# --- Sub-Agent Implementations ---

async def run_catalog_agent(query: str, user_id: int) -> str:
    """Agent specialized in catalog operations. Returns response_text."""
    llm = _client()
    tools = [search_books, check_availability, borrow_book, return_book, get_my_borrowed_books]
    llm_with_tools = llm.bind_tools(tools)
    
    system_prompt = (
        "You are the Library Catalog Agent for a real library system. "
        "You can search books, check availability, borrow books, return books, and list active loans.\n\n"
        "STRICT RULES — you must NEVER violate these:\n"
        "1. NEVER call return_book because a user CLAIMS they did not borrow a book or disputes a loan record. "
        "return_book must ONLY be called when the user explicitly says they are physically returning a book right now (e.g. 'I am returning this book', 'I want to return book X').\n"
        "2. If a user disputes or denies a loan (e.g. 'I didn't borrow that', 'that is an error', 'remove that from my account'), "
        "you must NOT modify any records. Instead, tell them: "
        "'I cannot remove loan records. If you believe there is an error with your account, please speak to a librarian at the front desk who can investigate and correct it.'\n"
        "3. You cannot delete, clear, or modify loan records for any reason other than an explicit physical return.\n\n"
        f"The current user's ID is {user_id}. You MUST pass this ID to any tool that requires a user_id.\n"
        "Answer concisely and always follow these rules without exception."
    )
    
    messages = [SystemMessage(content=system_prompt), HumanMessage(content=query)]
    
    for _ in range(3):
        try:
            ai_msg = await llm_with_tools.ainvoke(messages)
            messages.append(ai_msg)
            
            if not ai_msg.tool_calls:
                return ai_msg.content or "Task complete."
                
            for tc in ai_msg.tool_calls:
                tool_name = tc["name"]
                tool_args = tc["args"]
                
                tool_instance = next((t for t in tools if t.name == tool_name), None)
                if tool_instance:
                    res = tool_instance.invoke(tool_args)
                    messages.append(ToolMessage(content=str(res), tool_call_id=tc["id"], name=tool_name))
                else:
                    messages.append(ToolMessage(content=f"Error: Tool {tool_name} not found", tool_call_id=tc["id"], name=tool_name))
        except Exception as e:
            return f"Catalog Agent Error: {e}"
            
    return "Catalog Agent max loops reached."


async def run_policy_agent(query: str, user_id: int) -> tuple[str, list]:
    """Agent specialized in policy/knowledge base. Returns (response_text, retrieved_chunks)."""
    llm = _client()
    tools = [search_knowledge_base]
    llm_with_tools = llm.bind_tools(tools)
    
    system_prompt = "You are the Policy Agent. Use your search_knowledge_base tool to answer the user's questions about library rules, fees, hours, etc. Answer concisely based only on retrieved context."
    messages = [SystemMessage(content=system_prompt), HumanMessage(content=query)]
    
    kb_chunks = []
    
    for _ in range(3):
        try:
            ai_msg = await llm_with_tools.ainvoke(messages)
            messages.append(ai_msg)
            
            if not ai_msg.tool_calls:
                return ai_msg.content or "Task complete.", kb_chunks
                
            for tc in ai_msg.tool_calls:
                tool_name = tc["name"]
                tool_args = tc["args"]
                
                tool_instance = next((t for t in tools if t.name == tool_name), None)
                if tool_instance:
                    res = tool_instance.invoke(tool_args)
                    try:
                        parsed = json.loads(res)
                        if parsed.get("status") == "success":
                            kb_chunks.extend(parsed.get("results", []))
                    except Exception:
                        pass
                    messages.append(ToolMessage(content=str(res), tool_call_id=tc["id"], name=tool_name))
                else:
                    messages.append(ToolMessage(content=f"Error: Tool {tool_name} not found", tool_call_id=tc["id"], name=tool_name))
        except Exception as e:
            return f"Policy Agent Error: {e}", kb_chunks
            
    return "Policy Agent max loops reached.", kb_chunks


# --- Orchestrator Tools ---

@tool
def call_catalog_agent(query: str) -> str:
    """Route to the Library Catalog Specialist to handle finding books, checking availability, borrowing, returning, and listing active loans."""
    pass # Replaced by direct Orchestrator routing logic

@tool
def call_policy_agent(query: str) -> str:
    """Route to the Policy Specialist to search the knowledge base for library rules, fees, hours, and amenities."""
    pass # Replaced by direct Orchestrator routing logic


async def stream_reply(
    history: list[dict],
    user_message: str,
    user_id: int,
    retrieved_context: str = "",
) -> AsyncGenerator[str, None]:
    """Orchestrator stream_reply. Acts as a router."""
    if await is_harmful_input(user_message):
        yield "[Safety Warning: Content flagged.]"
        return

    llm = _client()
    orchestrator_tools = [call_catalog_agent, call_policy_agent]
    llm_with_tools = llm.bind_tools(orchestrator_tools)
    
    orchestrator_prompt = "You are the Orchestrator for the Library Assistant. Your job is routing, not answering. Delegate catalog queries to the Catalog Agent. Delegate policy/rules queries to the Policy Agent. If the user's message is a simple greeting, you can reply directly. DO NOT attempt to answer policy or catalog questions yourself. Use your routing tools."
    
    messages = [SystemMessage(content=orchestrator_prompt)]
    messages.extend(_to_langchain_history(history))
    messages.append(HumanMessage(content=user_message))

    kb_eval_data = {"question": user_message, "chunks": [], "error": None}

    MAX_ROUTING_HOPS = 3
    for _ in range(MAX_ROUTING_HOPS):
        try:
            ai_msg = await llm_with_tools.ainvoke(messages)
            
            if ai_msg.content:
                yield ai_msg.content
                
            messages.append(ai_msg)
            
            if not ai_msg.tool_calls:
                break
                
            for tc in ai_msg.tool_calls:
                name = tc["name"]
                args = tc["args"]
                query = args.get("query", user_message)
                
                if name == "call_catalog_agent":
                    yield "\n[STATUS:Delegating to Catalog Agent...]\n"
                    res_text = await run_catalog_agent(query, user_id)
                    messages.append(ToolMessage(content=res_text, tool_call_id=tc["id"], name=name))
                    
                elif name == "call_policy_agent":
                    yield "\n[STATUS:Delegating to Policy Agent...]\n"
                    res_text, chunks = await run_policy_agent(query, user_id)
                    kb_eval_data["chunks"].extend(chunks)
                    messages.append(ToolMessage(content=res_text, tool_call_id=tc["id"], name=name))
                    
                else:
                    messages.append(ToolMessage(content=f"Unknown agent: {name}", tool_call_id=tc["id"], name=name))
                    
        except Exception as e:
            yield f"\n\n[System Error: Orchestrator failed: {e}]"
            return
    else:
        yield "\n\n[System Warning: Max routing hops reached. Orchestrator forced to stop.]"

    # ── Precision / Recall Evaluation ─────────────────────────────────────────
    metrics = await evaluate_retrieval(kb_eval_data["question"], kb_eval_data["chunks"])
    yield f"[METRICS:{json.dumps(metrics)}]"


async def generate_chat_title(prompt: str) -> str:
    """Generate a short 3-5 word title for a new chat session based on the first prompt."""
    llm = _client("llama-3.1-8b-instant")
    messages = [
        SystemMessage(content="You are a helpful assistant that generates extremely short titles (2-5 words max) for a conversation based on the user's first message. Do NOT use quotes around the title. Do NOT add any preamble. Just output the short title."),
        HumanMessage(content=prompt)
    ]
    try:
        ai_msg = await llm.ainvoke(messages)
        title = ai_msg.content.strip().strip('"').strip("'")
        return title[:100]
    except Exception as e:
        print(f"[LLM Error] Failed to generate chat title: {e}")
        return prompt[:30] + ("..." if len(prompt) > 30 else "")
