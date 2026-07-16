import os
import tempfile
import pytest
import gc
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from backend.main import app
from backend.ai.parser import JSONParser, JSONParserError
from backend.tool_manager import ToolManager, ToolManagerError
from tools.notes.router import get_notes_service
from tools.notes.service import NotesService

@pytest.fixture
def temp_workspace():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a temp sqlite file for notes testing
        db_path = os.path.join(tmpdir, "test_notes.db")
        notes_service = NotesService(db_path=db_path)
        app.dependency_overrides[get_notes_service] = lambda: notes_service
        
        yield tmpdir, notes_service
        
        app.dependency_overrides.clear()
        del notes_service
        gc.collect()

@pytest.fixture
def client(temp_workspace):
    with TestClient(app) as c:
        yield c

# ----------------- Parser Tests -----------------

def test_json_parser_valid():
    raw_json = '{"tool": "file", "action": "find", "parameters": {"query": "resume.pdf"}}'
    intent = JSONParser.parse_intent(raw_json)
    assert intent.tool == "file"
    assert intent.action == "find"
    assert intent.parameters == {"query": "resume.pdf"}

def test_json_parser_valid_with_markdown():
    raw_markdown = '```json\n{"tool": "notes", "action": "create", "parameters": {"title": "Hello"}}\n```'
    intent = JSONParser.parse_intent(raw_markdown)
    assert intent.tool == "notes"
    assert intent.action == "create"
    assert intent.parameters == {"title": "Hello"}

def test_json_parser_invalid():
    # Not valid JSON
    with pytest.raises(JSONParserError):
        JSONParser.parse_intent("not a json string")
    
    # Missing required fields
    with pytest.raises(JSONParserError):
        JSONParser.parse_intent('{"tool": "notes"}')

# ----------------- Chat Endpoint Tests -----------------

@patch("backend.ai.llm.LLMService.generate_response")
def test_chat_endpoint_no_tool(mock_llm, client):
    # LLM decides no tool is needed and returns general chat intent
    mock_llm.return_value = '{"tool": "none", "action": "none", "parameters": {"message": "I am Echo AI."}}'
    
    response = client.post("/chat", json={"message": "Who are you?"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["tool"] == "none"
    assert data["result"] == "I am Echo AI."

@patch("backend.ai.llm.LLMService.generate_response")
def test_chat_endpoint_create_folder(mock_llm, client):
    # LLM routes to file tool create_folder
    mock_llm.return_value = '{"tool": "file", "action": "create_folder", "parameters": {"path": "DemoFolder"}}'
    
    response = client.post("/chat", json={"message": "Create a folder named DemoFolder"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["tool"] == "file"
    assert data["action"] == "create_folder"
    assert "DemoFolder" in data["result"]

@patch("backend.ai.llm.LLMService.generate_response")
def test_chat_endpoint_create_note(mock_llm, client):
    mock_llm.return_value = '{"tool": "notes", "action": "create", "parameters": {"title": "Shopping", "content": "Apples", "tags": ["grocery"]}}'
    
    response = client.post("/chat", json={"message": "Create a note called Shopping with content Apples"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["tool"] == "notes"
    assert data["action"] == "create"
    assert data["result"]["title"] == "Shopping"
    assert data["result"]["content"] == "Apples"

@patch("backend.ai.llm.LLMService.generate_response")
def test_chat_endpoint_system_cpu(mock_llm, client):
    mock_llm.return_value = '{"tool": "system", "action": "cpu", "parameters": {}}'
    
    response = client.post("/chat", json={"message": "Show CPU usage"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["tool"] == "system"
    assert data["action"] == "cpu"
    assert "percent_usage" in data["result"]

@patch("backend.ai.llm.LLMService.generate_response")
def test_chat_endpoint_browser_search(mock_llm, client):
    mock_llm.return_value = '{"tool": "browser", "action": "search", "parameters": {"query": "FastAPI", "max_results": 1}}'
    
    with patch("requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = '<div class="result"><a class="result__url" href="https://fastapi.tiangolo.com">FastAPI</a></div>'
        mock_get.return_value = mock_resp
        
        response = client.post("/chat", json={"message": "Search FastAPI"})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["tool"] == "browser"
        assert len(data["result"]) == 1
        assert "fastapi" in data["result"][0]["url"]

@patch("backend.ai.llm.LLMService.generate_response")
def test_chat_endpoint_unknown_tool(mock_llm, client):
    # Unknown tool returned
    mock_llm.return_value = '{"tool": "hacker_tool", "action": "hack", "parameters": {}}'
    
    response = client.post("/chat", json={"message": "Hack my computer"})
    # ToolManagerError mapping should throw a 400 Bad Request
    assert response.status_code == 400
    assert "unknown tool" in response.json()["detail"].lower()

@patch("backend.ai.llm.LLMService.generate_response")
def test_chat_endpoint_unknown_action(mock_llm, client):
    # Valid tool, unknown action
    mock_llm.return_value = '{"tool": "file", "action": "explode", "parameters": {"path": "test.txt"}}'
    
    response = client.post("/chat", json={"message": "Explode test.txt"})
    assert response.status_code == 400
    assert "unknown action" in response.json()["detail"].lower()

@patch("backend.ai.llm.LLMService.generate_response")
def test_chat_endpoint_malformed_json(mock_llm, client):
    # Malformed JSON from LLM
    mock_llm.return_value = "This is not json output."
    
    response = client.post("/chat", json={"message": "Show CPU"})
    assert response.status_code == 400
    assert "invalid json" in response.json()["detail"].lower()

@patch("backend.ai.llm.LLMService.generate_response")
def test_chat_endpoint_groq_failure(mock_llm, client):
    # Simulate API Key/Auth/Timeout failure
    mock_llm.side_effect = RuntimeError("Authentication failed with Groq API.")
    
    response = client.post("/chat", json={"message": "Hello"})
    assert response.status_code == 502
    assert "authentication failed" in response.json()["detail"].lower()

@patch("backend.ai.llm.LLMService.generate_response")
def test_notes_integration_flow(mock_llm, client):
    # 1. Create note
    mock_llm.return_value = '{"tool": "notes", "action": "create", "title": "Shopping List", "content": "milk"}'
    res = client.post("/chat", json={"message": "create note Shopping List with content milk"})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["result"]["title"] == "Shopping List"
    
    # 2. Read by exact title
    mock_llm.return_value = '{"tool": "notes", "action": "read", "title": "Shopping List"}'
    res = client.post("/chat", json={"message": "Show Shopping List note"})
    assert res.status_code == 200
    assert res.json()["result"]["title"] == "Shopping List"
    
    # 3. Read by lowercase title
    mock_llm.return_value = '{"tool": "notes", "action": "read", "title": "shopping list"}'
    res = client.post("/chat", json={"message": "Show shopping list note"})
    assert res.status_code == 200
    assert res.json()["result"]["title"] == "Shopping List"

    # 4. Update by title
    mock_llm.return_value = '{"tool": "notes", "action": "update", "title": "shopping list", "content": "milk and honey"}'
    res = client.post("/chat", json={"message": "Update shopping list to milk and honey"})
    assert res.status_code == 200
    assert res.json()["result"]["content"] == "milk and honey"
    
    # 5. Note not found
    mock_llm.return_value = '{"tool": "notes", "action": "read", "title": "Unknown Note"}'
    res = client.post("/chat", json={"message": "Show Unknown Note"})
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()

    # 6. Duplicate titles -> Clarification
    # Create another note with title "Shopping List"
    mock_llm.return_value = '{"tool": "notes", "action": "create", "title": "Shopping List", "content": "eggs"}'
    res = client.post("/chat", json={"message": "Create another Shopping List note"})
    assert res.status_code == 200
    
    # Now ask to read "Shopping List" -> should return requires_clarification
    mock_llm.return_value = '{"tool": "notes", "action": "read", "title": "Shopping List"}'
    res = client.post("/chat", json={"message": "Show Shopping List"})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is False
    assert data["requires_clarification"] is True
    assert len(data["options"]) == 2
    
    # 7. Fallback to newest note
    mock_llm.return_value = '{"tool": "notes", "action": "read", "title": "Shopping List", "fallback_to_newest": true}'
    res = client.post("/chat", json={"message": "Show Shopping List newest"})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["result"]["content"] == "eggs"

    # 8. Delete by title (using fallback_to_newest)
    mock_llm.return_value = '{"tool": "notes", "action": "delete", "title": "Shopping List", "fallback_to_newest": true}'
    res = client.post("/chat", json={"message": "Delete newest Shopping List"})
    assert res.status_code == 200
    
    # Now showing "Shopping List" should not require clarification anymore
    mock_llm.return_value = '{"tool": "notes", "action": "read", "title": "Shopping List"}'
    res = client.post("/chat", json={"message": "Show Shopping List"})
    assert res.status_code == 200
    assert res.json()["success"] is True
    assert res.json()["result"]["content"] == "milk and honey"

