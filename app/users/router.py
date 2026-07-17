from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.deps import get_current_user, get_current_admin_user
from .model import User
from .schemas import UserRead
from typing import List


router = APIRouter(tags=["Users"])


@router.get("/users/me", response_model=UserRead)
def get_me(current_user: User = Depends(get_current_user)):
    """Return the profile of the currently authenticated user."""
    return current_user


@router.get("/users/{user_id}", response_model=UserRead)
def get_user(user_id: int, db: Session = Depends(get_db)):
    """Fetch any user by their numeric ID."""
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.get("/api/admin/users", response_model=List[UserRead])
def get_all_users(db: Session = Depends(get_db), admin: User = Depends(get_current_admin_user)):
    """Admin-only: fetch all users."""
    return db.query(User).order_by(User.id.asc()).all()


@router.put("/api/admin/users/{user_id}/role", response_model=UserRead)
def toggle_user_admin_role(user_id: int, db: Session = Depends(get_db), admin: User = Depends(get_current_admin_user)):
    """Admin-only: toggle the is_admin status of a user."""
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Optional safety: prevent the only admin from removing their own admin status?
    # For now, just toggle it.
    user.is_admin = not user.is_admin
    db.commit()
    db.refresh(user)
    return user
