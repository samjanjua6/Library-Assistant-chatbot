from __future__ import annotations
from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship

from ..core.database import Base


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    author = Column(String, index=True, nullable=False)
    genre = Column(String, index=True)
    total_copies = Column(Integer, default=1)
    available_copies = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship to loans and holds
    loans = relationship("Loan", back_populates="book")
    holds = relationship("Hold", back_populates="book")


class Loan(Base):
    __tablename__ = "loans"

    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    borrowed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    due_date = Column(DateTime, nullable=False)
    returned_at = Column(DateTime, nullable=True)
    status = Column(String, default="borrowed") # "borrowed" or "returned"

    book = relationship("Book", back_populates="loans")
    user = relationship("User")


class Hold(Base):
    __tablename__ = "holds"

    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    placed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(String, default="active") # "active", "ready", "fulfilled", "cancelled"

    book = relationship("Book", back_populates="holds")
    user = relationship("User")
