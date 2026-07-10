# Simple FastAPI User API

A small FastAPI project with a single `users` table, basic signup/login endpoints, and a modular folder structure.

## What It Does

- Creates users with hashed passwords
- Authenticates by username or email
- Returns user details without exposing passwords
- Uses SQLite for local development

## Features

- `POST /signup` to create a user
- `POST /login` to authenticate and return a dummy token
- `GET /users/{user_id}` to fetch public user info
- Pydantic validation for request bodies
- SQLAlchemy ORM models
- Pytest coverage for the core API flows

## Project Structure

```text
app/
  core/
    database.py
    security.py
  models/
    __init__.py
    user.py
  routers/
    __init__.py
    auth.py
    users.py
  schemas/
    __init__.py
    auth.py
    user.py
  main.py
main.py
tests/
  test_main.py
```

## Requirements

- Python 3.14+
- FastAPI
- SQLAlchemy
- Uvicorn
- Pytest

## Setup

Create and activate a virtual environment, then install dependencies:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Run the App

Start the API from the project root:

```powershell
uvicorn main:app --reload
```

Then open:

- Swagger UI: http://127.0.0.1:8000/docs
- OpenAPI JSON: http://127.0.0.1:8000/openapi.json

## Endpoints

### `POST /signup`

Create a new user.

Example request:

```json
{
  "username": "alice",
  "email": "alice@example.com",
  "password": "secret1"
}
```

Example response:

```json
{
  "id": 1,
  "username": "alice",
  "email": "alice@example.com",
  "created_at": "2026-07-10T09:50:31.719947"
}
```

### `POST /login`

Authenticate with username or email plus password.

Example request:

```json
{
  "username_or_email": "alice",
  "password": "secret1"
}
```

Example response:

```json
{
  "access_token": "dummy-token-for-user-1",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "alice",
    "email": "alice@example.com",
    "created_at": "2026-07-10T09:50:31.719947"
  }
}
```

### `GET /users/{user_id}`

Fetch a user by id.

Example response:

```json
{
  "id": 1,
  "username": "alice",
  "email": "alice@example.com",
  "created_at": "2026-07-10T09:50:31.719947"
}
```

## Testing

Run the test suite with:

```powershell
pytest
```

The tests cover:

- OpenAPI/docs availability
- Successful signup, login, and user lookup
- Duplicate email rejection
- Wrong password rejection

## Notes

- Passwords are hashed before storage.
- The project uses SQLite and creates the schema at startup.
- The login token is intentionally dummy-only for now; real auth can be added later.