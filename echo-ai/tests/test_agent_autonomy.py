import os
import tempfile
import pytest
import gc
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from backend.main import app
from backend.planner.planner import Planner
from backend.planner.schemas import Plan, Task
from backend.agent.context import ExecutionContext
from backend.agent.executor import Executor
from backend.agent.loop import AgentLoop
from backend.memory.conversation_memory import ConversationMemory
from tools.notes.router import get_notes_service
from tools.notes.service import NotesService

@pytest.fixture
def temp_workspace():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_agent_notes.db")
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

# ----------------- Planner & Schema Tests -----------------

def test_planner_configuration():
    with patch.dict(os.environ, {"PLANNER_MODEL": "llama-override"}):
        planner = Planner()
        assert planner.llm_service.model_name == "llama-override"

def test_planner_tool_validation():
    # Invalid tool should raise validation error
    with pytest.raises(Exception):
        Task(step=1, tool="nonexistent_tool", action="read")
        
    # Invalid action for valid tool should raise validation error
    with pytest.raises(Exception):
        Task(step=1, tool="notes", action="hack")

# ----------------- Context Sharing Tests -----------------

def test_execution_context_resolutions():
    context = ExecutionContext()
    
    # Store mock output dict for step 1
    context.set_step_output(1, {"id": 42, "title": "Confidential note"})
    
    # Resolve parameters referencing step 1
    raw_params = {
        "note_id": "$step1_result.id",
        "description": "Output is: $step1_result.title",
        "short_ref": "$step1.id"
    }
    
    resolved = context.resolve_parameters(raw_params)
    assert resolved["note_id"] == 42
    assert resolved["description"] == "Output is: Confidential note"
    assert resolved["short_ref"] == 42

# ----------------- Executor & Retry Engine Tests -----------------

def test_executor_retry_logic():
    mock_tm = MagicMock()
    executor = Executor(tool_manager=mock_tm, max_retries=2)
    task = Task(step=1, tool="system", action="cpu")
    
    # 1. Permanent error (should NOT retry)
    mock_tm.execute_tool.side_effect = FileNotFoundError("Missing file")
    with pytest.raises(FileNotFoundError):
        executor.execute_task(task, {})
    assert mock_tm.execute_tool.call_count == 1
    
    # 2. Transient error (should retry up to max_retries)
    mock_tm.reset_mock()
    mock_tm.execute_tool.side_effect = ConnectionError("Network timeout")
    
    with patch("time.sleep") as mock_sleep:
        with pytest.raises(ConnectionError):
            executor.execute_task(task, {})
        # Total attempts: 1 initial + 2 retries = 3
        assert mock_tm.execute_tool.call_count == 3
        assert mock_sleep.call_count == 2

# ----------------- Conversation Memory Tests -----------------

def test_conversation_memory_context():
    memory = ConversationMemory()
    assert "No previous conversation" in memory.to_prompt_context()
    
    # Update note memory
    memory.update(tool="notes", action="create", params={"title": "Weekly Tasks"}, result={"title": "Weekly Tasks", "id": 1})
    # Update file memory
    memory.update(tool="file", action="create_folder", params={"path": "AgentFolder"}, result="/workspace/AgentFolder")
    
    prompt_ctx = memory.to_prompt_context()
    assert "Weekly Tasks" in prompt_ctx
    assert "AgentFolder" in prompt_ctx

# ----------------- Agent Loop & Multi-step Workflow Tests -----------------

@patch("backend.ai.llm.LLMService.generate_response")
def test_agent_multi_step_workflow(mock_llm, client):
    # Workflow plan:
    # Step 1: Create note "Autonomy Note"
    # Step 2: Update the created note's content to "Updated via step 1 resolution" using context passing
    plan_json = """{
        "steps": [
            {
                "step": 1,
                "tool": "notes",
                "action": "create",
                "parameters": {"title": "Autonomy Note", "content": "Initial"}
            },
            {
                "step": 2,
                "tool": "notes",
                "action": "update",
                "parameters": {"title": "Autonomy Note", "content": "Value of step 1 title is $step1_result.title"}
            }
        ]
    }"""
    mock_llm.return_value = plan_json
    
    response = client.post("/chat", json={"message": "create note and update it"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["tool"] == "notes"
    assert data["action"] == "update"
    
    # The final updated content should have resolved "$step1_result.title" to "Autonomy Note"
    assert data["result"]["content"] == "Value of step 1 title is Autonomy Note"

# ----------------- Clarification & Resume Tests -----------------

@patch("backend.ai.llm.LLMService.generate_response")
def test_clarification_pausing_and_resume(mock_llm, client):
    # Step 1: Create duplicate notes named "Dupe"
    mock_llm.return_value = '{"steps": [{"step": 1, "tool": "notes", "action": "create", "parameters": {"title": "Dupe", "content": "One"}}]}'
    res = client.post("/chat", json={"message": "create note"})
    assert res.status_code == 200
    
    mock_llm.return_value = '{"steps": [{"step": 1, "tool": "notes", "action": "create", "parameters": {"title": "Dupe", "content": "Two"}}]}'
    res = client.post("/chat", json={"message": "create another note"})
    assert res.status_code == 200

    # Step 2: Try updating "Dupe" without fallback - should trigger clarification pause
    mock_llm.return_value = '{"steps": [{"step": 1, "tool": "notes", "action": "update", "parameters": {"title": "Dupe", "content": "Updated"}}]}'
    res = client.post("/chat", json={"message": "update note Dupe"})
    assert res.status_code == 200
    data = res.json()
    
    assert data["success"] is False
    assert data["requires_clarification"] is True
    assert len(data["options"]) == 2
    session_id = data["session_id"]
    assert session_id is not None
    
    # Option IDs are assigned dynamically. Let's select the first option ID
    first_opt_id = data["options"][0]["id"]
    
    # Step 3: Send selection response to /chat with session_id to resume
    res = client.post("/chat", json={
        "message": f"Option {first_opt_id}",
        "session_id": session_id
    })
    assert res.status_code == 200
    resume_data = res.json()
    assert resume_data["success"] is True
    assert resume_data["tool"] == "notes"
    assert resume_data["action"] == "update"
    assert resume_data["result"]["id"] == first_opt_id
    assert resume_data["result"]["content"] == "Updated"
