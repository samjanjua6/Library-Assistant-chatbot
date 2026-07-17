from __future__ import annotations

# pyrefly: ignore [missing-import]
from fastapi import Depends, HTTPException, status
# pyrefly: ignore [missing-import]
from fastapi.security import OAuth2PasswordBearer
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session

from .database import get_db
from .security import decode_access_token
from ..users.model import User


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """FastAPI dependency: resolves a Bearer JWT from the Authorization header to a User row."""
    exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise exc
    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise exc
    user = db.get(User, int(user_id))
    if user is None:
        raise exc
    return user


def get_current_user_ws(token: str | None, db: Session) -> User | None:
    """WebSocket variant: returns None instead of raising (browsers cannot receive HTTP 401 on WS)."""
    if not token:
        return None
    payload = decode_access_token(token)
    if payload is None:
        return None
    user_id: str | None = payload.get("sub")
    if user_id is None:
        return None
    return db.get(User, int(user_id))


def get_current_admin_user(user: User = Depends(get_current_user)) -> User:
    """Dependency to ensure the current user is an administrator."""
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges"
        )
    return user
