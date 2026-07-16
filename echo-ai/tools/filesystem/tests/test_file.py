import os
import shutil
import tempfile
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from tools.filesystem.router import get_fs_service
from tools.filesystem.service import FilesystemService

@pytest.fixture
def temp_workspace():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create some test files and folders
        os.makedirs(os.path.join(tmpdir, "folder1"))
        os.makedirs(os.path.join(tmpdir, "folder2"))
        
        with open(os.path.join(tmpdir, "file1.txt"), "w") as f:
            f.write("Hello World")
            
        with open(os.path.join(tmpdir, "folder1", "file2.txt"), "w") as f:
            f.write("Nested file")
            
        yield tmpdir

@pytest.fixture
def client(temp_workspace):
    test_service = FilesystemService(base_dir=temp_workspace)
    app.dependency_overrides[get_fs_service] = lambda: test_service
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

def test_list_files(client):
    response = client.get("/file/list")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    names = [item["name"] for item in data]
    assert "folder1" in names
    assert "folder2" in names
    assert "file1.txt" in names

def test_list_files_nested(client):
    response = client.get("/file/list?path=folder1")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "file2.txt"

def test_find_files(client):
    response = client.post("/file/find", json={"path": "", "query": "file2"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "file2.txt"
    assert data[0]["path"].replace("\\", "/") == "folder1/file2.txt"

def test_create_folder(client):
    response = client.post("/file/create-folder", json={"path": "new_folder"})
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    
    response = client.get("/file/list")
    names = [item["name"] for item in response.json()]
    assert "new_folder" in names

def test_rename(client):
    response = client.post("/file/rename", json={"path": "file1.txt", "new_name": "renamed_file.txt"})
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    
    response = client.get("/file/list")
    names = [item["name"] for item in response.json()]
    assert "renamed_file.txt" in names
    assert "file1.txt" not in names

def test_move(client):
    response = client.post("/file/move", json={"src_path": "file1.txt", "dest_path": "folder1/file1_moved.txt"})
    assert response.status_code == 200
    
    response = client.get("/file/list?path=folder1")
    names = [item["name"] for item in response.json()]
    assert "file1_moved.txt" in names

def test_copy(client):
    response = client.post("/file/copy", json={"src_path": "file1.txt", "dest_path": "file1_copy.txt"})
    assert response.status_code == 200
    
    response = client.get("/file/list")
    names = [item["name"] for item in response.json()]
    assert "file1.txt" in names
    assert "file1_copy.txt" in names

def test_delete(client):
    response = client.post("/file/delete", json={"path": "file1.txt"})
    assert response.status_code == 200
    
    response = client.get("/file/list")
    names = [item["name"] for item in response.json()]
    assert "file1.txt" not in names

def test_safe_path_violation(client):
    response = client.get("/file/list?path=../")
    assert response.status_code == 403
