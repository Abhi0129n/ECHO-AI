import os
import tempfile
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from tools.gmail.router import get_gmail_service
from tools.gmail.service import GmailService
from tools.gmail.utils import extract_email, format_subject, save_attachment

@pytest.fixture
def client():
    with tempfile.TemporaryDirectory() as tmpdir:
        test_service = GmailService(base_dir=tmpdir)
        app.dependency_overrides[get_gmail_service] = lambda: test_service
        
        yield TestClient(app), tmpdir
        
        app.dependency_overrides.clear()

def test_utils(client):
    _, tmpdir = client
    assert extract_email("John Doe <john@example.com>") == "john@example.com"
    assert extract_email("simple@example.com") == "simple@example.com"
    
    assert format_subject("Hello") == "Re: Hello"
    assert format_subject("Re: Hello") == "Re: Hello"
    
    # Save attachment using base64 for "hello" (aGVsbG8=)
    path = save_attachment("aGVsbG8=", "test.txt", tmpdir)
    full_path = os.path.join(tmpdir, path)
    assert os.path.exists(full_path)
    with open(full_path, "r", encoding="utf-8") as f:
        assert f.read() == "hello"

def test_unread_endpoint(client):
    c, _ = client
    response = c.get("/gmail/unread?limit=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["id"] == "msg123"
    assert data[0]["is_unread"] is True

def test_search_endpoint(client):
    c, _ = client
    response = c.get("/gmail/search?q=important&limit=1")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == "msg123"

def test_message_details_endpoint(client):
    c, _ = client
    response = c.get("/gmail/message/msg123")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "msg123"
    assert "Mock Subject msg123" in data["subject"]
    assert "Hello! This is a mock email body." in data["body_text"]

def test_send_endpoint(client):
    c, _ = client
    response = c.post("/gmail/send", json={
        "recipient": "recipient@example.com",
        "subject": "Hello Test",
        "body": "This is a test email body."
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["message_id"] == "msg_sent_999"

def test_reply_endpoint(client):
    c, _ = client
    response = c.post("/gmail/reply?message_id=msg123", json={
        "body": "This is a reply email body."
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["message_id"] == "msg_sent_999"

def test_archive_endpoint(client):
    c, _ = client
    response = c.post("/gmail/archive?message_id=msg123")
    assert response.status_code == 200
    assert response.json()["status"] == "success"

def test_delete_endpoint(client):
    c, _ = client
    response = c.delete("/gmail/message/msg123")
    assert response.status_code == 204

def test_download_attachment_endpoint(client):
    c, tmpdir = client
    response = c.post("/gmail/attachments?message_id=msg123&attachment_id=att456&filename=mock_doc.txt")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    
    # Verify file saved in tmpdir/echo-ai/uploads/attachments/mock_doc.txt
    full_path = os.path.join(tmpdir, data["file_path"])
    assert os.path.exists(full_path)
    with open(full_path, "r", encoding="utf-8") as f:
        # data "dGVzdF9hdHRhY2htZW50X2NvbnRlbnQ=" is base64 for "test_attachment_content"
        assert f.read() == "test_attachment_content"
