from __future__ import annotations

import asyncio
import json
from openai import AsyncOpenAI

from ..core.config import settings


def _client() -> AsyncOpenAI:
    return AsyncOpenAI(api_key=settings.GROQ_API_KEY, base_url="https://api.cerebras.ai/v1")


async def evaluate_retrieval(question: str, chunks: list[dict]) -> dict:
    """
    LLM-as-a-Judge: evaluates the quality of knowledge base retrieval
    for a given question.

    Returns a dict with precision, recall, f1_score, relevant_chunks, total_chunks.
    Falls back to None values on any error so it never blocks the main chat.
    """
    if not chunks:
        return {
            "precision": None, "recall": None, "f1_score": None,
            "relevant_chunks": 0, "total_chunks": 0
        }

    total = len(chunks)

    # Build a numbered list of chunk texts for the prompt
    chunks_text = "\n\n".join(
        f"Chunk {i+1}:\n{c.get('text', '')[:600]}"  # cap at 600 chars per chunk
        for i, c in enumerate(chunks)
    )

    prompt = f"""You are an expert RAG evaluation system. Your job is to evaluate retrieval quality.

User Question: {question}

Retrieved Chunks:
{chunks_text}

Evaluate the retrieval and respond ONLY with a valid JSON object (no explanation, no markdown):
{{
  "chunk_relevance": [<true or false for each chunk, in order>],
  "recall": <float 0.0-1.0 estimating how completely the question can be answered from these chunks>
}}

Rules:
- chunk_relevance must have exactly {total} boolean values
- recall 1.0 means the chunks contain everything needed to fully answer the question
- recall 0.0 means the chunks contain nothing useful"""

    try:
        client = _client()
        response = await asyncio.wait_for(
            client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "You are a JSON-only RAG evaluation assistant. Output only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                max_tokens=150,
                stream=False,
            ),
            timeout=8.0  # hard timeout — never block the main chat
        )

        raw = response.choices[0].message.content.strip()

        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]

        result = json.loads(raw)
        relevance: list[bool] = result.get("chunk_relevance", [])
        recall: float = float(result.get("recall", 0.0))

        # Validate lengths
        if len(relevance) != total:
            relevance = [True] * total  # fallback: assume all relevant

        relevant = sum(1 for r in relevance if r)
        precision = relevant / total if total > 0 else 0.0
        recall = max(0.0, min(1.0, recall))

        # F1 Score
        if (precision + recall) > 0:
            f1 = 2 * (precision * recall) / (precision + recall)
        else:
            f1 = 0.0

        return {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1, 4),
            "relevant_chunks": relevant,
            "total_chunks": total,
        }

    except asyncio.TimeoutError:
        print("[Evaluator] Timed out — skipping metrics for this response.")
    except json.JSONDecodeError as e:
        print(f"[Evaluator] JSON parse error: {e}")
    except Exception as e:
        print(f"[Evaluator] Unexpected error: {e}")

    return {
        "precision": None, "recall": None, "f1_score": None,
        "relevant_chunks": 0, "total_chunks": total
    }
