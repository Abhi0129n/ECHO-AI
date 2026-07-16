import os
import tempfile
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from backend.main import app
from tools.browser.router import get_browser_service
from tools.browser.service import BrowserService
from tools.browser.utils import is_valid_url

MOCK_HTML_CONTENT = """
<html>
    <head><title>Test Mock Title</title></head>
    <body>
        <h1>Welcome to Mock Land</h1>
        <p>This is some visible text about apples and bananas.</p>
        <a href="https://example.com/document.pdf">Download PDF here</a>
        <a href="/other-page">Regular link</a>
        <style>body { color: red; }</style>
        <script>alert("hello");</script>
    </body>
</html>
"""

@pytest.fixture
def client():
    with tempfile.TemporaryDirectory() as tmpdir:
        test_service = BrowserService(base_dir=tmpdir)
        app.dependency_overrides[get_browser_service] = lambda: test_service
        
        with TestClient(app) as c:
            yield c, tmpdir
            
        app.dependency_overrides.clear()

def test_is_valid_url():
    assert is_valid_url("http://google.com") is True
    assert is_valid_url("https://localhost:8000/docs") is True
    assert is_valid_url("ftp://google.com") is False
    assert is_valid_url("google.com") is False

@patch("requests.get")
def test_google_search(mock_get, client):
    c, _ = client
    
    # Mock DuckDuckGo HTML search response
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = """
    <div class="result">
        <a class="result__url" href="https://example.com/python-info">Python Info Page</a>
        <a class="result__snippet" href="#">Python is a great programming language.</a>
    </div>
    """
    mock_get.return_value = mock_resp
    
    response = c.post("/browser/search", json={
        "query": "python",
        "max_results": 1
    })
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Python Info Page"
    assert data[0]["url"] == "https://example.com/python-info"
    assert "great programming language" in data[0]["snippet"]

@patch("requests.get")
def test_read_page(mock_get, client):
    c, _ = client
    
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = MOCK_HTML_CONTENT
    mock_get.return_value = mock_resp
    
    response = c.post("/browser/read", json={
        "url": "https://example.com"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Mock Title"
    assert "Welcome to Mock Land" in data["visible_text"]
    assert "apples and bananas" in data["visible_text"]
    assert "alert" not in data["visible_text"]
    
    # Verify PDF links extracted
    assert len(data["pdf_links"]) == 1
    assert data["pdf_links"][0]["url"] == "https://example.com/document.pdf"
    assert data["pdf_links"][0]["text"] == "Download PDF here"

@patch("requests.get")
def test_download_pdf(mock_get, client):
    c, tmpdir = client
    
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.iter_content = lambda chunk_size: [b"MOCK PDF DATA"]
    mock_get.return_value = mock_resp
    
    response = c.post("/browser/download-pdf", json={
        "url": "https://example.com/document.pdf",
        "output_filename": "test.pdf"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    
    # Verify file saved in tmpdir/echo-ai/uploads/test.pdf
    expected_path = os.path.join(tmpdir, data["file_path"])
    assert os.path.exists(expected_path)
    with open(expected_path, "rb") as f:
        assert f.read() == b"MOCK PDF DATA"
