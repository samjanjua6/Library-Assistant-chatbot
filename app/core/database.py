from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool

from .config import settings


def _build_database_url() -> "str | URL":
    """Build the DB URL from settings. Returns a URL object for Postgres
    (to preserve the password correctly) or a plain string for SQLite."""
    if settings.DATABASE_URL:
        # Explicit DSN (e.g. sqlite+pysqlite:///:memory: in tests)
        return settings.DATABASE_URL

    # Return the URL object directly — do NOT call str() on it.
    # str(URL) masks the password as '***', causing auth failures.
    return URL.create(
        "postgresql+pg8000",
        username=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT,
        database=settings.POSTGRES_DB,
    )


def _is_sqlite(url: "str | URL") -> bool:
    if isinstance(url, str):
        return url.startswith("sqlite")
    return url.drivername.startswith("sqlite")


DATABASE_URL = _build_database_url()

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if _is_sqlite(DATABASE_URL) else {},
    poolclass=StaticPool if _is_sqlite(DATABASE_URL) else None,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
