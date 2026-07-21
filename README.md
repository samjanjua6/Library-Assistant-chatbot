# 📚 Library Assistant Chatbot

A production-grade, full-stack AI chatbot for library management, powered by a **multi-agent orchestrator** architecture with **Cerebras AI (Gemma 4)**, **FastAPI**, **PostgreSQL**, **Google OAuth 2.0**, and a premium **React** frontend.

---

## ✨ Key Features

1. **Multi-Agent Orchestrator**: A three-tier AI system — a routing Orchestrator delegates queries to two specialist sub-agents: the **Catalog Agent** (books, loans) and the **Policy Agent** (rules, fees, hours).
2. **RAG-Powered Knowledge Base**: The Policy Agent uses Retrieval-Augmented Generation (RAG) with a chunked, vector-indexed knowledge base of library policy documents for accurate, grounded answers.
3. **Real-time Streaming WebSockets**: Streams response tokens directly to the chat bubble as they are generated, with live status indicators when agents are being dispatched.
4. **Catalog Management Tools**: The Catalog Agent can search books, check availability, borrow a book, return a book, and list a user's active loans — all via structured tool calls.
5. **Langfuse Observability**: Full LLM tracing with `@observe` decorators typed as `agent` for the Agent Graph view. Tracks latency, token usage, and cost per sub-agent via the `langfuse.openai` auto-instrumentation wrapper.
6. **RAG Evaluation Metrics**: Each Policy Agent response is evaluated for Precision, Recall, and F1 score against retrieved knowledge base chunks and streamed to the frontend.
7. **Google OAuth 2.0 & JWT**: Supports both traditional email/password login and seamless Google Sign-In. All REST and WebSocket endpoints are secured with signed JSON Web Tokens.
8. **Exponential Retry with Backoff**: All Cerebras API calls use automatic retries with jitter to gracefully handle rate limits (429) and timeouts.
9. **Max-Hop Guardrail**: The orchestrator enforces a `MAX_ROUTING_HOPS = 3` cap to prevent runaway routing loops.
10. **Docker Deployment**: Containerised with Docker Compose, fronted by Caddy as a reverse proxy with automatic HTTPS.

---

## 🏗️ Architecture

```
User Message (WebSocket)
        │
        ▼
  ┌─────────────┐
  │ Orchestrator │  ← routes, never answers directly
  └──────┬──────┘
         │
    ┌────┴─────┐
    │          │
    ▼          ▼
┌────────┐  ┌────────┐
│Catalog │  │Policy  │
│ Agent  │  │ Agent  │
└───┬────┘  └───┬────┘
    │            │
    ▼            ▼
DB Tools     RAG Search
(Search,     (Vector KB
Borrow,      + Gemma 4)
Return...)
```

---

## 📂 Directory Overview

```text
Library-Assistant-chatbot/
├── app/
│   ├── auth/               # Login, Signup & Google OAuth router
│   ├── chat/               # WebSocket router, orchestrator, sub-agents, prompts
│   ├── core/               # DB config, security utilities, JWT guards
│   ├── library/            # Catalog tools, RAG engine, evaluator, document ingestion
│   ├── users/              # User DB model & profile router
│   └── main.py             # App entry point
├── frontend-src/           # React frontend source (Vite)
│   └── src/
│       ├── components/     # Sidebar, MessageBubble, TopBar, etc.
│       ├── contexts/       # Theme context
│       └── pages/          # Landing, Login, Chat pages
├── frontend/dist/          # Compiled static bundle served by FastAPI
├── .github/workflows/      # GitHub Actions CI/CD pipeline for Azure deployment
├── docker-compose.yml      # Docker Compose (web + Caddy)
├── Dockerfile
├── requirements.txt
└── build.sh
```

---

## ⚙️ Setup & Local Installation

### 1. Requirements
- Python 3.11+
- Node.js 18+ (for building React)
- PostgreSQL database

### 2. Backend Setup

```powershell
# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Create your .env file
copy .env.example .env
```

Fill in your `.env` credentials:

| Variable | Description |
|---|---|
| `GROQ_API_KEY` | Your Cerebras Cloud API key |
| `DATABASE_URL` | PostgreSQL connection string |
| `SECRET_KEY` | A random secret for JWT signing |
| `GOOGLE_CLIENT_ID` | Google Cloud Console OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | Google Cloud Console OAuth client secret |
| `GOOGLE_REDIRECT_URI` | `http://localhost:8000/auth/google/callback` for local dev |
| `LANGFUSE_PUBLIC_KEY` | *(Optional)* Langfuse project public key |
| `LANGFUSE_SECRET_KEY` | *(Optional)* Langfuse project secret key |
| `LANGFUSE_BASE_URL` | *(Optional)* `https://cloud.langfuse.com` |

> **Note:** Langfuse keys are optional. If not provided, tracing is gracefully disabled and the application runs normally.

### 3. Frontend Build

```powershell
cd frontend-src
npm install
npm run build
cd ..
```

*This compiles the React app into `frontend/dist/` which FastAPI serves as a static SPA.*

### 4. Run the Server

```powershell
uvicorn app.main:app --reload
```

| URL | Description |
|---|---|
| `http://localhost:8000/` | Landing Page |
| `http://localhost:8000/login` | Sign In / Sign Up |
| `http://localhost:8000/chat` | AI Library Assistant |
| `http://localhost:8000/docs` | Interactive Swagger API Docs |

---

## 🐳 Docker Deployment

```bash
# Build and start all containers
sudo docker compose up --build -d

# Restart the app container
sudo docker restart library-container
```

---

## 🧪 Testing

```powershell
pytest -v
```

Tests use an in-memory SQLite database — no live PostgreSQL connection needed.

---

## 🔭 Observability with Langfuse

When Langfuse keys are configured, every chat request produces a nested trace in your [Langfuse dashboard](https://cloud.langfuse.com):

```
orchestrator (agent)
├── catalog_agent (agent)
│   └── LLM call: gemma-4-31b (generation)
│       └── search_books (tool)
└── policy_agent (agent)
    └── LLM call: gemma-4-31b (generation)
        └── search_knowledge_base (tool)
```

This lets you compare cost, latency, and token usage **per sub-agent**, not just as a single total.

---

## 🔗 Links

- **GitHub**: [samjanjua6/Library-Assistant-chatbot](https://github.com/samjanjua6/Library-Assistant-chatbot)
