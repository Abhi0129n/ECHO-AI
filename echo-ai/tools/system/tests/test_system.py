import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from backend.main import app
from tools.system.router import get_system_service
from tools.system.service import SystemService
from tools.system.utils import bytes_to_gb, validate_app

@pytest.fixture
def client():
    test_service = SystemService()
    app.dependency_overrides[get_system_service] = lambda: test_service
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

def test_utils():
    assert bytes_to_gb(1073741824) == 1.0
    assert bytes_to_gb(1610612736) == 1.5
    
    assert validate_app("notepad.exe") is True
    assert validate_app("C:\\Windows\\notepad.exe") is True
    assert validate_app("notepad.exe; rm -rf /") is False
    assert validate_app("calc.exe & echo Hacked") is False

def test_cpu_endpoint(client):
    response = client.get("/system/cpu")
    assert response.status_code == 200
    data = response.json()
    assert "percent_usage" in data
    assert "cores_logical" in data

def test_memory_endpoint(client):
    response = client.get("/system/memory")
    assert response.status_code == 200
    data = response.json()
    assert "total_gb" in data
    assert "percent_used" in data

def test_disk_endpoint(client):
    response = client.get("/system/disk")
    assert response.status_code == 200
    data = response.json()
    assert "total_gb" in data
    assert "percent_used" in data

def test_battery_endpoint(client):
    response = client.get("/system/battery")
    assert response.status_code == 200
    data = response.json()
    assert "percent" in data

def test_processes_endpoint(client):
    response = client.get("/system/processes?limit=3")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= 3
    if len(data) > 0:
        assert "pid" in data[0]
        assert "name" in data[0]

def test_apps_endpoint(client):
    response = client.get("/system/apps")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

@patch("subprocess.Popen")
def test_open_app_endpoint(mock_popen, client):
    # Mock subprocess.Popen returning a mock process with pid
    mock_process = MagicMock()
    mock_process.pid = 1234
    mock_popen.return_value = mock_process
    
    response = client.post("/system/open", json={
        "app_name": "notepad.exe",
        "args": ["test.txt"]
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["pid"] == 1234
    assert data["app_name"] == "notepad.exe"

@patch("psutil.process_iter")
def test_close_app_endpoint(mock_process_iter, client):
    # Mock process_iter
    mock_proc = MagicMock()
    mock_proc.info = {"name": "notepad.exe", "pid": 1234}
    mock_process_iter.return_value = [mock_proc]
    
    response = client.post("/system/close", json={
        "app_name": "notepad.exe"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["terminated_count"] == 1
    assert data["app_name"] == "notepad.exe"
    
    # Assert terminate was called
    mock_proc.terminate.assert_called_once()
