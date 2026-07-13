# Zylo — FastAPI Chat

A full-stack FastAPI project featuring **JWT authentication**, a **secured WebSocket chat**, and a polished two-page browser frontend.

## Features

- `POST /signup` — register a new user
- `POST /login` — authenticate and receive a signed **JWT**
- `GET /users/me` — fetch the current user (requires Bearer token)
- `GET /users/{user_id}` — fetch any user by ID
- `WS /ws/chat?token=<jwt>` — authenticated WebSocket chat; rejects connections without a valid token (close code 1008)

## Frontend

The frontend is a **React + Tailwind CSS** SPA built with Vite, served by FastAPI from `frontend/dist/`.

Key design rules enforced in the components:
- **State separation** — only one form (Login or Signup) is ever mounted at a time
- **Segmented pill** at the top of the card switches between the two states
- **Accent gradient** (`indigo→violet`) is used **only** on primary CTA buttons (`SubmitButton`) — nowhere else
- Inputs have transparent-dark backgrounds and a subtle indigo focus ring
- Card sits on a deeper canvas (`#0c0e17`) with a lighter surface (`#13161f`)

### Component tree

```
App (Router)
├── AuthPage        — Login/Signup container + pill control
│   ├── LoginForm   — username/password fields
│   ├── SignupForm  — username/email/password fields
│   ├── InputField  — reusable labeled input primitive
│   └── SubmitButton — gradient CTA (the only accent element)
└── ChatPage        — WebSocket orchestration
    ├── TopBar      — brand, WS status dot, user info, logout
    ├── MessageList — scrollable message bubbles
    └── ChatInput   — floating input bar + send button
```

## Project Structure

```text
.
├── main.py                    # Uvicorn entry point
├── requirements.txt
├── .env.example               # Copy to .env and fill in your values
├── .gitignore
├── app/
│   ├── main.py                # FastAPI app factory
│   ├── core/
│   │   ├── config.py          # Pydantic-settings (reads .env)
│   │   ├── database.py        # SQLAlchemy engine + session
│   │   ├── security.py        # Password hashing + JWT create/decode
│   │   └── deps.py            # Reusable FastAPI dependencies
│   ├── models/
│   │   └── user.py            # User ORM model
│   ├── routers/
│   │   ├── auth.py            # /signup  /login
│   │   ├── chat.py            # /ws/chat (auth-secured)
│   │   └── users.py           # /users/me  /users/{id}
│   └── schemas/
│       ├── auth.py            # LoginRequest  TokenResponse
│       └── user.py            # UserSignup  UserRead
├── frontend/
│   ├── index.html             # Login / Sign-up page
│   ├── chat.html              # Chat page (requires JWT in localStorage)
│   ├── styles.css             # Shared styles (Inter font, dark glass)
│   ├── app.js                 # Auth page logic
│   └── chat.js                # Chat page logic (WebSocket + auth guard)
└── tests/
    ├── test_main.py
    └── test_websocket_chat.py
```

## Requirements

- Python 3.11+
- PostgreSQL (running locally)

## Quick Start

```powershell
# 1. Create & activate virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# 2. Install dependencies
python -m pip install -r requirements.txt

# 3. Configure (optional — defaults match a local Postgres install)
copy .env.example .env
# Edit .env with your POSTGRES_PASSWORD, SECRET_KEY, etc.

# 4. Start the server
uvicorn main:app --reload
```

Open:

| Page | URL |
|---|---|
| Login / Sign-up | http://127.0.0.1:8000/ |
| Chat | http://127.0.0.1:8000/chat |
| Swagger UI | http://127.0.0.1:8000/docs |

## Database Configuration

The app resolves the connection string in this order:

1. `DATABASE_URL` env var (takes priority — used by tests with SQLite)
2. Individual `POSTGRES_*` vars (or defaults below)

Default local PostgreSQL connection:

| Setting | Default |
|---|---|
| Host | `localhost` |
| Port | `5433` |
| Database | `Testing` |
| User | `postgres` |
| Password | `12345` |

## Authentication Flow

1. **Sign up** → `POST /signup` — creates user, returns public profile
2. **Log in** → `POST /login` — verifies credentials, returns a signed **JWT**
3. **Use token** → pass as `Authorization: Bearer <token>` header for REST endpoints, or as `?token=<token>` query param for WebSocket connections
4. **JWT expires** after `ACCESS_TOKEN_EXPIRE_MINUTES` (default: 60 min). The chat page automatically redirects to login when the server closes with code 1008.

## WebSocket Security

```
ws://localhost:8000/ws/chat?token=<your_jwt>
```

- ✅ Valid token → connection accepted, greeted by name
- ❌ Missing / invalid token → server closes with **code 1008** (Policy Violation)

## Running Tests

Tests use SQLite in-memory — no Postgres needed.

```powershell
pytest -v
```

## Generating a Secure SECRET_KEY

```powershell
.venv\Scripts\python.exe -c "import secrets; print(secrets.token_hex(32))"
```

Paste the output as `SECRET_KEY` in your `.env` file.# ai-chatbot
