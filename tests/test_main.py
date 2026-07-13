from __future__ import annotations

import os

# Must be set before any app import so pydantic-settings picks it up
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")

import pytest
from fastapi.testclient import TestClient
from jose import jwt

from app.core.config import settings
from app.core.database import Base, engine
from app.main import app


client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


# ── helpers ───────────────────────────────────────────────────────────────

def _signup(username="alice", email="alice@example.com", password="supersecret"):
    return client.post(
        "/signup",
        json={"username": username, "email": email, "password": password},
    )


def _login(identifier="alice", password="supersecret"):
    return client.post(
        "/login",
        json={"username_or_email": identifier, "password": password},
    )


# ── tests ─────────────────────────────────────────────────────────────────

def test_openapi_docs_exposes_expected_endpoints():
    assert client.get("/").status_code == 200
    assert client.get("/docs").status_code == 200

    paths = client.get("/openapi.json").json()["paths"]
    assert "/signup" in paths
    assert "/login" in paths
    assert "/users/{user_id}" in paths
    assert "/users/me" in paths


def test_signup_login_and_get_user_flow():
    # Signup
    res = _signup()
    assert res.status_code == 201
    user = res.json()
    assert user["username"] == "alice"
    assert user["email"] == "alice@example.com"
    assert "hashed_password" not in user

    # Login — returns a real JWT now
    res = _login()
    assert res.status_code == 200
    data = res.json()

    token = data["access_token"]
    assert data["token_type"] == "bearer"
    assert data["user"]["username"] == "alice"
    assert "hashed_password" not in data["user"]

    # Validate the JWT is signed and contains the correct sub claim
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert payload["sub"] == str(user["id"])

    # GET /users/{id}
    res = client.get(f"/users/{user['id']}")
    assert res.status_code == 200
    fetched = res.json()
    assert fetched["id"] == user["id"]
    assert fetched["username"] == "alice"
    assert "hashed_password" not in fetched


def test_get_users_me_requires_auth():
    res = client.get("/users/me")
    assert res.status_code == 401


def test_get_users_me_with_valid_token():
    _signup()
    token = _login().json()["access_token"]

    res = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json()["username"] == "alice"


def test_signup_rejects_duplicate_email():
    _signup()
    res = _signup(username="alice2")  # same email
    assert res.status_code == 400


def test_login_rejects_wrong_password():
    _signup()
    res = _login(password="wrongpassword")
    assert res.status_code == 401


def test_user_not_found():
    res = client.get("/users/999")
    assert res.status_code == 404
