from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .core.database import Base, engine
from .models import User  # noqa: F401 — registers model with SQLAlchemy metadata
from .routers import auth, chat, users


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Zylo — FastAPI Chat",
    description="A secure chat app with JWT-authenticated WebSocket and a React + Tailwind frontend.",
    version="2.0.0",
)

app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(users.router)

# ── Static files ──────────────────────────────────────────────────────────────
# The React + Vite SPA builds to frontend/dist/.
# /assets  → frontend/dist/assets  (Vite JS/CSS bundles)
frontend_dist   = Path(__file__).resolve().parent.parent / "frontend" / "dist"
frontend_assets = frontend_dist / "assets"

app.mount("/assets", StaticFiles(directory=frontend_assets), name="assets")

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:8000",
        "http://localhost:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── SPA routes ────────────────────────────────────────────────────────────────
def _spa() -> FileResponse:
    """Return the React SPA shell — React Router handles client-side routing."""
    return FileResponse(frontend_dist / "index.html")


@app.get("/", include_in_schema=False)
def home():
    """Login / Sign-up page (React SPA)."""
    return _spa()


@app.get("/chat", include_in_schema=False)
def chat_page():
    """Chat page (React SPA — auth guard runs in the browser)."""
    return _spa()
