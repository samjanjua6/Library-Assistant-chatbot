from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.database import Base, engine
from app.main import app


client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_openapi_docs_exposes_all_three_endpoints():
    response = client.get("/")
    assert response.status_code == 200

    response = client.get("/docs")
    assert response.status_code == 200

    openapi_response = client.get("/openapi.json")
    assert openapi_response.status_code == 200
    paths = openapi_response.json()["paths"]
    assert "/signup" in paths
    assert "/login" in paths
    assert "/users/{user_id}" in paths


def test_signup_login_and_get_user_flow():
    signup_response = client.post(
        "/signup",
        json={"username": "alice", "email": "alice@example.com", "password": "supersecret"},
    )
    assert signup_response.status_code == 201
    created_user = signup_response.json()
    assert created_user["username"] == "alice"
    assert created_user["email"] == "alice@example.com"
    assert "hashed_password" not in created_user

    login_response = client.post(
        "/login",
        json={"username_or_email": "alice", "password": "supersecret"},
    )
    assert login_response.status_code == 200
    login_data = login_response.json()
    assert login_data["access_token"].startswith("dummy-token-for-user-")
    assert login_data["user"]["username"] == "alice"
    assert "hashed_password" not in login_data["user"]

    user_response = client.get(f"/users/{created_user['id']}")
    assert user_response.status_code == 200
    fetched_user = user_response.json()
    assert fetched_user["id"] == created_user["id"]
    assert fetched_user["username"] == "alice"
    assert fetched_user["email"] == "alice@example.com"
    assert "hashed_password" not in fetched_user


def test_signup_rejects_duplicate_email():
    first_response = client.post(
        "/signup",
        json={"username": "alice", "email": "alice@example.com", "password": "supersecret"},
    )
    assert first_response.status_code == 201

    duplicate_response = client.post(
        "/signup",
        json={"username": "alice2", "email": "alice@example.com", "password": "supersecret"},
    )
    assert duplicate_response.status_code == 400


def test_login_rejects_wrong_password():
    client.post(
        "/signup",
        json={"username": "alice", "email": "alice@example.com", "password": "supersecret"},
    )

    login_response = client.post(
        "/login",
        json={"username_or_email": "alice", "password": "wrongpassword"},
    )
    assert login_response.status_code == 401
