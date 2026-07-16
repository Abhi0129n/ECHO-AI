import os
import tempfile
import pytest
import gc
from fastapi.testclient import TestClient
from backend.main import app
from tools.notes.router import get_notes_service
from tools.notes.service import NotesService
from tools.notes.schemas import NoteCreate, NoteUpdate

@pytest.fixture
def temp_db():
    fd, db_path = tempfile.mkstemp()
    os.close(fd)
    
    test_service = NotesService(db_path=db_path)
    yield test_service
    
    # Run garbage collector to ensure connection handles are released
    gc.collect()
    
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except PermissionError:
            # Under Windows, open sqlite files are locked until process ends
            pass

@pytest.fixture
def client(temp_db):
    app.dependency_overrides[get_notes_service] = lambda: temp_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

def test_create_note(client):
    response = client.post("/notes/create", json={
        "title": "Shopping List",
        "content": "Buy apples and milk",
        "tags": ["groceries", "personal"]
    })
    assert response.status_code == 201
    data = response.json()
    assert data["id"] is not None
    assert data["title"] == "Shopping List"
    assert data["content"] == "Buy apples and milk"
    assert data["tags"] == ["groceries", "personal"]

def test_read_note_all(client):
    client.post("/notes/create", json={"title": "Note 1", "content": "Content 1", "tags": []})
    client.post("/notes/create", json={"title": "Note 2", "content": "Content 2", "tags": []})
    
    response = client.get("/notes/read")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2

def test_read_note_by_id(client):
    create_res = client.post("/notes/create", json={"title": "Get Me", "content": "Find this", "tags": ["tag1"]})
    note_id = create_res.json()["id"]
    
    response = client.get(f"/notes/read?id={note_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == note_id
    assert data["title"] == "Get Me"

def test_read_note_not_found(client):
    response = client.get("/notes/read?id=999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

def test_update_note(client):
    create_res = client.post("/notes/create", json={"title": "Old Title", "content": "Old Content", "tags": []})
    note_id = create_res.json()["id"]
    
    response = client.put(f"/notes/update?id={note_id}", json={
        "title": "New Title",
        "content": "New Content",
        "tags": ["updated"]
    })
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "New Title"
    assert data["content"] == "New Content"
    assert data["tags"] == ["updated"]

def test_delete_note(client):
    create_res = client.post("/notes/create", json={"title": "To Delete", "content": "Delete me", "tags": []})
    note_id = create_res.json()["id"]
    
    response = client.delete(f"/notes/delete?id={note_id}")
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    
    response = client.get(f"/notes/read?id={note_id}")
    assert response.status_code == 404

def test_search_notes(client):
    client.post("/notes/create", json={"title": "Apples", "content": "Red apples", "tags": ["fruit"]})
    client.post("/notes/create", json={"title": "Bananas", "content": "Yellow fruit", "tags": []})
    
    response = client.get("/notes/search?q=Apples")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Apples"
    
    response = client.get("/notes/search?q=fruit")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
