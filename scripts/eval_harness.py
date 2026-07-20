"""
RAG Evaluation Harness
======================
Tests multiple retrieval configurations against a fixed eval set and produces
a detailed Markdown report in chunking_test_report.md.

Configurations varied:
  - Chunking strategy: fixed-size sliding window vs. sentence-aware
  - Chunk size & overlap
  - top_k (n_results)
  - Re-ranking (keyword-boost re-sort)
  - Hybrid (dense + BM25 keyword) vs. vector-only

Run from the project root:
    .venv\\Scripts\\python.exe scripts\\eval_harness.py
"""

from __future__ import annotations

import sys
import os
import json
import time
import math
import asyncio
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# ── Path setup ────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.library.rag import (
    KNOWLEDGE_BASE_DIR,
    SUPPORTED_EXTENSIONS,
    extract_text,
    sliding_window_chunker,
    clear_knowledge_base,
    collection,
    ingest_documents,
)
from app.core.config import settings
# pyrefly: ignore [missing-import]
from openai import AsyncOpenAI

# ── Eval Question Set ─────────────────────────────────────────────────────────
EVAL_QUESTIONS = [
    {
        "id": "TC1",
        "category": "Needle-in-Haystack (Specific Detail)",
        "question": "What is the exact processing fee if I return a book with severe water damage?",
        "expected_keywords": ["10", "processing fee", "severe", "damage"],
    },
    {
        "id": "TC2",
        "category": "Broad Context (Summary)",
        "question": "Can you summarize all the financial penalties associated with late, lost, and damaged books?",
        "expected_keywords": ["late fee", "lost", "damage", "replacement", "administrative"],
    },
    {
        "id": "TC3",
        "category": "Boundary Condition (Cross-chunk answer)",
        "question": "If I lose a book, what is the exact step-by-step process and fee structure I must follow?",
        "expected_keywords": ["lost", "30 days", "replacement cost", "10", "administrative"],
    },
    {
        "id": "TC4",
        "category": "Multi-hop (Requires combining two rules)",
        "question": "Can I borrow a 4th book if I renew one of my current loans?",
        "expected_keywords": ["3", "maximum", "renew", "active loans"],
    },
    {
        "id": "TC5",
        "category": "Negative / Edge Case",
        "question": "What happens to my account if I have more than $20 in outstanding late fees?",
        "expected_keywords": ["suspended", "20", "borrowing privileges"],
    },
]

# ── Configurations to test ────────────────────────────────────────────────────
CONFIGURATIONS = [
    # Fixed-size, small chunks
    {"id": "CFG-1",  "strategy": "fixed",    "chunk_size": 500,  "overlap": 50,  "top_k": 3, "rerank": False, "hybrid": False},
    {"id": "CFG-2",  "strategy": "fixed",    "chunk_size": 500,  "overlap": 50,  "top_k": 5, "rerank": False, "hybrid": False},
    # Fixed-size, medium chunks
    {"id": "CFG-3",  "strategy": "fixed",    "chunk_size": 1000, "overlap": 200, "top_k": 3, "rerank": False, "hybrid": False},
    {"id": "CFG-4",  "strategy": "fixed",    "chunk_size": 1000, "overlap": 200, "top_k": 5, "rerank": False, "hybrid": False},
    {"id": "CFG-5",  "strategy": "fixed",    "chunk_size": 1000, "overlap": 200, "top_k": 3, "rerank": True,  "hybrid": False},
    # Fixed-size, large chunks
    {"id": "CFG-6",  "strategy": "fixed",    "chunk_size": 2000, "overlap": 400, "top_k": 3, "rerank": False, "hybrid": False},
    # Sentence-aware chunking
    {"id": "CFG-7",  "strategy": "sentence", "chunk_size": 5,   "overlap": 1,   "top_k": 3, "rerank": False, "hybrid": False},
    {"id": "CFG-8",  "strategy": "sentence", "chunk_size": 5,   "overlap": 1,   "top_k": 5, "rerank": True,  "hybrid": False},
    # Hybrid: dense + keyword
    {"id": "CFG-9",  "strategy": "fixed",    "chunk_size": 1000, "overlap": 200, "top_k": 3, "rerank": False, "hybrid": True},
    {"id": "CFG-10", "strategy": "fixed",    "chunk_size": 1000, "overlap": 200, "top_k": 5, "rerank": True,  "hybrid": True},
]

REPORT_PATH = Path(r"C:\Users\samja\.gemini\antigravity\brain\8657ab1d-762e-4b42-9642-40a3e90f9334\chunking_test_report.md")

# ── LLM client ────────────────────────────────────────────────────────────────
def _llm_client():
    return AsyncOpenAI(api_key=settings.GROQ_API_KEY, base_url="https://api.cerebras.ai/v1")


# ── Sentence-aware chunker ────────────────────────────────────────────────────
def sentence_chunker(text: str, sentences_per_chunk: int = 5, overlap_sentences: int = 1) -> list[str]:
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    sentences = [s.strip() for s in sentences if s.strip()]
    chunks = []
    step = max(1, sentences_per_chunk - overlap_sentences)
    for i in range(0, len(sentences), step):
        chunk = " ".join(sentences[i:i + sentences_per_chunk])
        if chunk:
            chunks.append(chunk)
    return chunks


# ── BM25 keyword scorer ───────────────────────────────────────────────────────
def bm25_score(query: str, text: str, k1: float = 1.5, b: float = 0.75, avg_dl: int = 500) -> float:
    query_terms = query.lower().split()
    words = text.lower().split()
    dl = len(words)
    score = 0.0
    for term in query_terms:
        tf = words.count(term)
        if tf == 0:
            continue
        idf = math.log(2.0)  # simplified single-corpus IDF
        numerator = tf * (k1 + 1)
        denominator = tf + k1 * (1 - b + b * dl / avg_dl)
        score += idf * numerator / denominator
    return score


# ── Ingestion ─────────────────────────────────────────────────────────────────
def build_collection(cfg: Dict) -> int:
    print(f"  [Ingest] strategy={cfg['strategy']}, size={cfg['chunk_size']}, overlap={cfg['overlap']}")
    clear_knowledge_base()

    documents, metadatas, ids = [], [], []

    for file_path in sorted(KNOWLEDGE_BASE_DIR.iterdir()):
        if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        content = extract_text(file_path)
        if not content.strip():
            continue

        if cfg["strategy"] == "sentence":
            chunks = sentence_chunker(content,
                                      sentences_per_chunk=cfg["chunk_size"],
                                      overlap_sentences=cfg["overlap"])
        else:
            chunks = sliding_window_chunker(content,
                                            chunk_size=cfg["chunk_size"],
                                            chunk_overlap=cfg["overlap"])

        for i, chunk in enumerate(chunks):
            if not chunk.strip():
                continue
            doc_id = f"{file_path.stem}_{cfg['id']}_{i}"
            documents.append(chunk)
            metadatas.append({"source": file_path.name, "chunk_index": i})
            ids.append(doc_id)

    if documents:
        collection.upsert(documents=documents, metadatas=metadatas, ids=ids)
    print(f"  [Ingest] {len(documents)} chunks loaded.")
    return len(documents)


# ── Retrieval ─────────────────────────────────────────────────────────────────
def retrieve(query: str, cfg: Dict) -> List[Dict]:
    top_k = cfg["top_k"]
    fetch_k = min(top_k * 3, 20) if (cfg["hybrid"] or cfg["rerank"]) else top_k

    try:
        results = collection.query(query_texts=[query], n_results=fetch_k)
    except Exception as e:
        print(f"  [Retrieve] Error: {e}")
        return []

    chunks = []
    if results and results["documents"]:
        for i, text in enumerate(results["documents"][0]):
            meta = (results["metadatas"][0][i] if results["metadatas"] else {})
            dist = (results["distances"][0][i] if results["distances"] else 1.0)
            chunks.append({
                "rank": i + 1,
                "source": meta.get("source", "Unknown"),
                "chunk_index": meta.get("chunk_index", i),
                "text": text,
                "vector_distance": round(dist, 4),
                "bm25_score": 0.0,
                "final_score": round(max(0, 1 - dist), 4),
            })

    # Hybrid: blend BM25 score
    if cfg["hybrid"]:
        for c in chunks:
            bm25 = bm25_score(query, c["text"])
            c["bm25_score"] = round(bm25, 4)
            c["final_score"] = round(0.6 * c["final_score"] + 0.4 * min(bm25, 1.0), 4)
        chunks.sort(key=lambda x: x["final_score"], reverse=True)
        for i, c in enumerate(chunks):
            c["rank"] = i + 1

    # Filter clearly irrelevant chunks
    chunks = [c for c in chunks if c["vector_distance"] < 1.5]

    # Keyword-boost re-ranking
    if cfg["rerank"] and chunks:
        query_terms = set(query.lower().split())
        for c in chunks:
            hits = sum(1 for t in query_terms if t in c["text"].lower())
            boost = hits / max(1, len(query_terms))
            c["final_score"] = round(c["final_score"] * (1 + 0.3 * boost), 4)
        chunks.sort(key=lambda x: x["final_score"], reverse=True)
        for i, c in enumerate(chunks):
            c["rank"] = i + 1

    return chunks[:top_k]


# ── LLM Answer Generation ─────────────────────────────────────────────────────
async def generate_answer(question: str, chunks: List[Dict]) -> str:
    if not chunks:
        return "_No relevant context retrieved — answer skipped._"

    context = "\n\n---\n\n".join(
        f"[Source: {c['source']}, Chunk #{c['chunk_index']}]\n{c['text']}"
        for c in chunks
    )
    prompt = (
        f"Answer the following question using ONLY the context provided. "
        f"If the answer is not present, say: 'I don't have that information.'\n\n"
        f"Context:\n{context}\n\nQuestion: {question}\nAnswer:"
    )

    client = _llm_client()
    try:
        resp = await asyncio.wait_for(
            client.chat.completions.create(
                model="gemma-4-31b",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=300,
            ),
            timeout=30.0,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"_LLM call failed: {e}_"


# ── Scoring ───────────────────────────────────────────────────────────────────
def score_retrieval(chunks: List[Dict], expected_keywords: List[str]) -> Dict:
    if not chunks:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0, "relevant": 0, "total": 0}

    combined = " ".join(c["text"].lower() for c in chunks)
    relevant = sum(
        1 for c in chunks
        if any(kw.lower() in c["text"].lower() for kw in expected_keywords)
    )
    found_kw = sum(1 for kw in expected_keywords if kw.lower() in combined)

    p = relevant / len(chunks)
    r = found_kw / len(expected_keywords) if expected_keywords else 0.0
    f1 = (2 * p * r / (p + r)) if (p + r) > 0 else 0.0

    return {
        "precision": round(p * 100, 1),
        "recall": round(r * 100, 1),
        "f1": round(f1 * 100, 1),
        "relevant": relevant,
        "total": len(chunks),
    }


# ── Report Builder ────────────────────────────────────────────────────────────
def build_report(all_results: List[Dict], run_meta: Dict) -> str:
    lines = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines += [
        "# RAG Chunking & Retrieval Evaluation Report",
        "",
        f"**Generated:** {now}  ",
        f"**Total configurations tested:** {len(CONFIGURATIONS)}  ",
        f"**Total questions:** {len(EVAL_QUESTIONS)}  ",
        f"**Total runs:** {len(all_results)}  ",
        "",
        "---",
        "",
        "## 📋 Configuration Overview",
        "",
        "| ID | Strategy | Chunk Size / Sentences | Overlap | top\\_k | Re-rank | Hybrid |",
        "| :--- | :--- | :---: | :---: | :---: | :---: | :---: |",
    ]
    for cfg in CONFIGURATIONS:
        lines.append(
            f"| **{cfg['id']}** | {cfg['strategy']} | {cfg['chunk_size']} | {cfg['overlap']} "
            f"| {cfg['top_k']} | {'✅' if cfg['rerank'] else '❌'} | {'✅' if cfg['hybrid'] else '❌'} |"
        )

    lines += ["", "---", ""]

    # Group by question
    by_q: Dict[str, Dict] = {}
    for r in all_results:
        qid = r["question_id"]
        if qid not in by_q:
            by_q[qid] = {"meta": r["question_meta"], "cfgs": []}
        by_q[qid]["cfgs"].append(r)

    for qid, qdata in by_q.items():
        meta = qdata["meta"]
        lines += [
            f"## 🧪 {qid}: {meta['category']}",
            "",
            f"**Question:** *\"{meta['question']}\"*",
            f"**Expected keywords:** `{', '.join(meta['expected_keywords'])}`",
            "",
            "### Metrics Comparison",
            "",
            "| Config | Strategy | Size | Overlap | top\\_k | Rerank | Hybrid | Precision (%) | Recall (%) | F1 (%) | Relevant/Total |",
            "| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
        ]
        for r in qdata["cfgs"]:
            cfg = r["config"]
            s = r["scores"]
            lines.append(
                f"| **{cfg['id']}** | {cfg['strategy']} | {cfg['chunk_size']} | {cfg['overlap']} "
                f"| {cfg['top_k']} | {'✅' if cfg['rerank'] else '❌'} | {'✅' if cfg['hybrid'] else '❌'} "
                f"| {s['precision']}% | {s['recall']}% | {s['f1']}% | {s['relevant']}/{s['total']} |"
            )

        lines += ["", "### Retrieved Chunks & Answers (Expandable)", ""]

        for r in qdata["cfgs"]:
            cfg = r["config"]
            chunks = r["chunks"]
            answer = r["answer"]
            label = (
                f"**{cfg['id']}** — {cfg['strategy']}, size={cfg['chunk_size']}, "
                f"overlap={cfg['overlap']}, top_k={cfg['top_k']}, "
                f"rerank={'on' if cfg['rerank'] else 'off'}, hybrid={'on' if cfg['hybrid'] else 'off'}"
            )
            lines += [
                "<details>",
                f"<summary>{label}</summary>",
                "",
                "**Retrieved Chunks (ranked order):**",
                "",
            ]
            if chunks:
                for c in chunks:
                    snippet = c["text"][:350].replace("\n", " ")
                    if len(c["text"]) > 350:
                        snippet += "..."
                    lines += [
                        f"**#{c['rank']}** `{c['source']}` chunk\\#{c['chunk_index']} "
                        f"| vec\\_dist=`{c['vector_distance']}` bm25=`{c['bm25_score']}` score=`{c['final_score']}`",
                        "",
                        f"> {snippet}",
                        "",
                    ]
            else:
                lines += ["_No chunks passed the distance filter._", ""]

            lines += [
                "**Final Answer:**",
                "",
                f"> {answer}",
                "",
                "</details>",
                "",
            ]

        lines += ["---", ""]

    # Overall summary
    lines += [
        "## 📊 Overall Summary — Best Config per Question",
        "",
        "| Question | Best Config | Strategy | Size | Precision | Recall | F1 |",
        "| :--- | :--- | :--- | :---: | :---: | :---: | :---: |",
    ]
    for qid, qdata in by_q.items():
        best = max(qdata["cfgs"], key=lambda r: r["scores"]["f1"])
        s = best["scores"]
        c = best["config"]
        lines.append(
            f"| {qid} | **{c['id']}** | {c['strategy']} | {c['chunk_size']} "
            f"| {s['precision']}% | {s['recall']}% | **{s['f1']}%** |"
        )

    # Avg F1 per config
    lines += [
        "",
        "## 🏆 Average F1 Score per Configuration (across all questions)",
        "",
        "| Config | Avg Precision | Avg Recall | Avg F1 |",
        "| :--- | :---: | :---: | :---: |",
    ]
    cfg_ids = [c["id"] for c in CONFIGURATIONS]
    for cfg_id in cfg_ids:
        runs = [r for r in all_results if r["config"]["id"] == cfg_id]
        if not runs:
            continue
        avg_p = round(sum(r["scores"]["precision"] for r in runs) / len(runs), 1)
        avg_r = round(sum(r["scores"]["recall"] for r in runs) / len(runs), 1)
        avg_f = round(sum(r["scores"]["f1"] for r in runs) / len(runs), 1)
        lines.append(f"| **{cfg_id}** | {avg_p}% | {avg_r}% | **{avg_f}%** |")

    lines += [
        "",
        "---",
        "",
        "## ✅ Conclusions & Recommendations",
        "",
        "*(Fill in after reviewing the tables above.)*",
        "",
        "**1. Best config for specific fact retrieval:**",
        "- Config ID: _____  Why: _____",
        "",
        "**2. Best config for broad/summary questions:**",
        "- Config ID: _____  Why: _____",
        "",
        "**3. Did hybrid search outperform vector-only?**",
        "- _____",
        "",
        "**4. Did re-ranking improve precision?**",
        "- _____",
        "",
        "**5. Sentence-aware vs. fixed-size chunking?**",
        "- _____",
        "",
        "**6. Final recommended production configuration:**",
        "- Strategy: _____",
        "- Chunk Size: _____",
        "- Overlap: _____",
        "- top_k: _____",
        "- Re-rank: _____",
        "- Hybrid: _____",
        "",
    ]

    return "\n".join(lines)


# ── Main ──────────────────────────────────────────────────────────────────────
async def run_harness():
    print("=" * 60)
    print("  RAG EVALUATION HARNESS")
    print(f"  Configurations : {len(CONFIGURATIONS)}")
    print(f"  Questions      : {len(EVAL_QUESTIONS)}")
    print(f"  Total runs     : {len(CONFIGURATIONS) * len(EVAL_QUESTIONS)}")
    print("=" * 60)

    all_results = []
    run_meta = {"started": datetime.now().isoformat()}

    for cfg in CONFIGURATIONS:
        print(f"\n▶ {cfg['id']}")
        build_collection(cfg)
        time.sleep(0.5)

        for q in EVAL_QUESTIONS:
            print(f"  ▸ {q['id']} {q['question'][:55]}...")
            chunks = retrieve(q["question"], cfg)
            scores = score_retrieval(chunks, q["expected_keywords"])
            answer = await generate_answer(q["question"], chunks)

            all_results.append({
                "question_id": q["id"],
                "question_meta": q,
                "config": cfg,
                "chunks": chunks,
                "scores": scores,
                "answer": answer,
            })

            print(
                f"     P={scores['precision']}%  R={scores['recall']}%  "
                f"F1={scores['f1']}%  chunks={scores['total']}"
            )
            await asyncio.sleep(0.3)

    print("\n📝 Building report...")
    report = build_report(all_results, run_meta)
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"✅ Report saved: {REPORT_PATH}")

    # Restore default KB
    print("\n↩  Restoring default KB (size=1000, overlap=200)...")
    clear_knowledge_base()
    ingest_documents(chunk_size=1000, chunk_overlap=200)
    print("✅ Done.")


if __name__ == "__main__":
    asyncio.run(run_harness())
