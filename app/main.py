from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .core.database import Base, engine
from .models import User
from .routers import auth, chat, users


Base.metadata.create_all(bind=engine)

app = FastAPI(title="Simple FastAPI User API")
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(users.router)

frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/frontend", StaticFiles(directory=frontend_dir), name="frontend")


@app.get("/")
def home():
	return FileResponse(frontend_dir / "index.html")

app.add_middleware(
	CORSMiddleware,
	allow_origins=["http://127.0.0.1:5500", "http://localhost:5500", "http://127.0.0.1:8000", "http://localhost:8000"],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)
