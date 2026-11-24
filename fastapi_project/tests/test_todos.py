"""CRUD tests for the FastAPI Todo API, against an in-memory SQLite database."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.database import get_db
from app.main import app

TODO = {"title": "Buy milk", "description": "Remember to stop at the store", "completed": False}


@pytest.fixture
def client():
    # One shared in-memory connection, so every request sees the same tables.
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)

    def get_test_db():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db] = get_test_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_root_links_docs(client):
    body = client.get("/").json()
    assert body["docs"] == "/docs"


def test_create_todo(client):
    response = client.post("/todos/", json=TODO)
    assert response.status_code == 201
    body = response.json()
    assert body["id"] == 1
    assert {k: body[k] for k in TODO} == TODO


def test_create_todo_requires_title_and_description(client):
    assert client.post("/todos/", json={"title": "No description"}).status_code == 422


def test_list_todos(client):
    client.post("/todos/", json=TODO)
    client.post("/todos/", json={**TODO, "title": "Walk the dog"})
    titles = [t["title"] for t in client.get("/todos/").json()]
    assert titles == ["Buy milk", "Walk the dog"]


def test_get_todo(client):
    todo_id = client.post("/todos/", json=TODO).json()["id"]
    response = client.get(f"/todos/{todo_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Buy milk"


def test_update_todo_changes_only_sent_fields(client):
    todo_id = client.post("/todos/", json=TODO).json()["id"]
    response = client.put(f"/todos/{todo_id}", json={"completed": True})
    assert response.status_code == 200
    body = response.json()
    assert body["completed"] is True
    assert body["title"] == TODO["title"]


def test_delete_todo(client):
    todo_id = client.post("/todos/", json=TODO).json()["id"]
    assert client.delete(f"/todos/{todo_id}").status_code == 204
    assert client.get(f"/todos/{todo_id}").status_code == 404


@pytest.mark.parametrize("method", ["get", "put", "delete"])
def test_missing_todo_is_404(client, method):
    kwargs = {"json": {"completed": True}} if method == "put" else {}
    response = getattr(client, method)("/todos/999", **kwargs)
    assert response.status_code == 404
    assert response.json()["detail"] == "Todo with id 999 not found"
