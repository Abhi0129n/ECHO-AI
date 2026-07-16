import os
import tempfile
import pytest
import fitz  # PyMuPDF
from fastapi.testclient import TestClient
from backend.main import app
from tools.pdf.router import get_pdf_service
from tools.pdf.service import PDFService
from tools.pdf.utils import page_range_validator

@pytest.fixture
def temp_pdf():
    # Create a valid PDF with PyMuPDF
    fd, pdf_path = tempfile.mkstemp(suffix=".pdf")
    os.close(fd)
    
    doc = fitz.open()
    page1 = doc.new_page()
    page1.insert_text((50, 50), "Echo AI PDF Tool Test Document. Page 1 content containing bananas.")
    
    page2 = doc.new_page()
    page2.insert_text((50, 50), "Second page of the PDF tool test. Page 2 content containing apples.")
    
    doc.save(pdf_path)
    doc.close()
    
    yield pdf_path
    
    if os.path.exists(pdf_path):
        os.remove(pdf_path)

@pytest.fixture
def client(temp_pdf):
    # Relative path from base_dir which will be set to the temp folder parent or root
    temp_dir = os.path.dirname(temp_pdf)
    rel_pdf_path = os.path.basename(temp_pdf)
    
    test_service = PDFService(base_dir=temp_dir)
    app.dependency_overrides[get_pdf_service] = lambda: test_service
    
    with TestClient(app) as c:
        yield c, rel_pdf_path
        
    app.dependency_overrides.clear()

def test_page_range_validator():
    assert page_range_validator("1-2, 4", 5) == [0, 1, 3]
    assert page_range_validator("3-5", 5) == [2, 3, 4]
    assert page_range_validator(None, 3) == [0, 1, 2]

def test_read_pdf(client):
    c, rel_pdf_path = client
    response = c.post("/pdf/read", json={
        "path": rel_pdf_path
    })
    assert response.status_code == 200
    data = response.json()
    assert data["page_count"] == 2
    assert len(data["pages"]) == 2
    assert "bananas" in data["pages"][0]["text"]
    assert "apples" in data["pages"][1]["text"]

def test_read_pdf_with_range(client):
    c, rel_pdf_path = client
    response = c.post("/pdf/read", json={
        "path": rel_pdf_path,
        "page_range": "2"
    })
    assert response.status_code == 200
    data = response.json()
    assert len(data["pages"]) == 1
    assert data["pages"][0]["page_number"] == 2
    assert "apples" in data["pages"][0]["text"]

def test_search_pdf(client):
    c, rel_pdf_path = client
    response = c.post("/pdf/search", json={
        "path": rel_pdf_path,
        "query": "bananas"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "bananas"
    assert len(data["results"]) == 1
    assert data["results"][0]["page_number"] == 1
    assert "bananas" in data["results"][0]["snippet"]

def test_read_pdf_not_found(client):
    c, _ = client
    response = c.post("/pdf/read", json={
        "path": "non_existent.pdf"
    })
    assert response.status_code == 404
