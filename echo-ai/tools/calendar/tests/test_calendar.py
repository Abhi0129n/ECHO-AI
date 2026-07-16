import os
import tempfile
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from backend.main import app
from tools.calendar.router import get_calendar_service
from tools.calendar.service import CalendarService
from tools.calendar.utils import validate_iso_format, find_free_slots

@pytest.fixture
def client():
    with tempfile.TemporaryDirectory() as tmpdir:
        test_service = CalendarService(base_dir=tmpdir)
        app.dependency_overrides[get_calendar_service] = lambda: test_service
        
        yield TestClient(app)
        
        app.dependency_overrides.clear()

def test_utils():
    assert validate_iso_format("2026-07-07T10:00:00") is True
    assert validate_iso_format("2026-07-07T10:00:00Z") is True
    assert validate_iso_format("invalid-time") is False
    
    # Test Free Slots Finder
    start = datetime(2026, 7, 7, 9, 0, 0)
    end = datetime(2026, 7, 7, 12, 0, 0)
    busy = [
        (datetime(2026, 7, 7, 10, 0, 0), datetime(2026, 7, 7, 11, 0, 0))
    ]
    duration = timedelta(minutes=30)
    
    slots = find_free_slots(busy, start, end, duration)
    assert len(slots) == 2
    assert slots[0] == (start, busy[0][0])
    assert slots[1] == (busy[0][1], end)

def test_today_events_endpoint(client):
    response = client.get("/calendar/today")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["id"] == "event1"
    assert data[0]["summary"] == "Weekly Status Meeting"

def test_search_events_endpoint(client):
    response = client.get("/calendar/search?q=Weekly")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == "event1"

def test_create_event_endpoint(client):
    now_date = datetime.now().strftime("%Y-%m-%d")
    response = client.post("/calendar/create", json={
        "summary": "Meeting with Client",
        "start_time": f"{now_date}T15:00:00Z",
        "end_time": f"{now_date}T16:00:00Z",
        "attendees": ["client@example.com"],
        "reminders": [{"method": "popup", "minutes_before": 15}]
    })
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == "new_event_123"
    assert data["summary"] == "Meeting with Client"
    assert data["reminders"][0]["minutes_before"] == 15

def test_update_event_endpoint(client):
    response = client.put("/calendar/update?event_id=event1", json={
        "summary": "Updated Meeting Summary",
        "location": "Zoom Link"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "event1"
    assert data["summary"] == "Updated Meeting Summary"
    assert data["location"] == "Zoom Link"

def test_move_event_endpoint(client):
    now_date = datetime.now().strftime("%Y-%m-%d")
    response = client.post("/calendar/move", json={
        "event_id": "event1",
        "start_time": f"{now_date}T17:00:00Z",
        "end_time": f"{now_date}T18:00:00Z"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "event1"
    assert "17:00:00" in data["start_time"]
    assert "18:00:00" in data["end_time"]

def test_delete_event_endpoint(client):
    response = client.delete("/calendar/delete?event_id=event1")
    assert response.status_code == 204

def test_free_slots_endpoint(client):
    now_date = datetime.now().strftime("%Y-%m-%d")
    response = client.get(f"/calendar/free-slots?start_time={now_date}T09:00:00Z&end_time={now_date}T12:00:00Z&duration_minutes=30")
    assert response.status_code == 200
    data = response.json()
    # Mock search events lists event1 from 10:00 to 11:00.
    # Therefore, 09:00 to 10:00 (free) and 11:00 to 12:00 (free).
    assert len(data) == 2
    assert "09:00:00" in data[0]["start"]
    assert "10:00:00" in data[0]["end"]
    assert "11:00:00" in data[1]["start"]
    assert "12:00:00" in data[1]["end"]
