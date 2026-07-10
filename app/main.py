from __future__ import annotations

from fastapi import FastAPI

from .core.database import Base, engine
from .models import User
from .routers import auth, users


Base.metadata.create_all(bind=engine)

app = FastAPI(title="Simple FastAPI User API")
app.include_router(auth.router)
app.include_router(users.router)
