import os
import csv
import tempfile
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from tools.productivity.router import get_productivity_service
from tools.productivity.service import ProductivityService

@pytest.fixture
def client():
    with tempfile.TemporaryDirectory() as tmpdir:
        test_service = ProductivityService(base_dir=tmpdir)
        app.dependency_overrides[get_productivity_service] = lambda: test_service
        
        yield TestClient(app), tmpdir
        
        app.dependency_overrides.clear()

def test_create_excel(client):
    c, tmpdir = client
    dest_path = "test_sheets.xlsx"
    
    response = c.post("/productivity/excel", json={
        "path": dest_path,
        "data": {
            "Sheet1": [
                ["Name", "Age"],
                ["Alice", 30],
                ["Bob", 25]
            ],
            "Sheet2": [
                ["Product", "Price"],
                ["Apple", 1.2],
                ["Orange", 1.5]
            ]
        }
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    
    # Verify file existence in temp workspace
    full_path = os.path.join(tmpdir, dest_path)
    assert os.path.exists(full_path)

def test_create_word(client):
    c, tmpdir = client
    dest_path = "test_doc.docx"
    
    response = c.post("/productivity/word", json={
        "path": dest_path,
        "title": "My Title",
        "content": [
            {"text": "Introduction", "is_heading": True, "heading_level": 1},
            {"text": "This is standard text content.", "is_heading": False}
        ]
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    
    # Verify file existence
    full_path = os.path.join(tmpdir, dest_path)
    assert os.path.exists(full_path)

def test_create_powerpoint(client):
    c, tmpdir = client
    dest_path = "test_presentation.pptx"
    
    response = c.post("/productivity/powerpoint", json={
        "path": dest_path,
        "title": "Welcome Slide",
        "subtitle": "An ECHO AI Presentation",
        "slides": [
            {"title": "Overview", "content": "- Bullet point A\n- Bullet point B"}
        ]
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    
    # Verify file existence
    full_path = os.path.join(tmpdir, dest_path)
    assert os.path.exists(full_path)

def test_read_csv(client):
    c, tmpdir = client
    csv_filename = "data.csv"
    csv_full_path = os.path.join(tmpdir, csv_filename)
    
    # Write a test CSV file
    with open(csv_full_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Item"])
        writer.writerow(["1", "Keyboard"])
        writer.writerow(["2", "Mouse"])
        
    response = c.post("/productivity/csv/read", json={
        "path": csv_filename
    })
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert data[0] == ["ID", "Item"]
    assert data[1] == ["1", "Keyboard"]
    assert data[2] == ["2", "Mouse"]

def test_read_csv_not_found(client):
    c, _ = client
    response = c.post("/productivity/csv/read", json={
        "path": "non_existent_file.csv"
    })
    assert response.status_code == 404
