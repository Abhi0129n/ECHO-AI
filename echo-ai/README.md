# Echo AI - Agentic AI Operating System

Echo AI is an Agentic AI Operating System built using Python, FastAPI, and SQLite. 

---

## Folder Structure

- `backend/`: Core service logic and API routers.
  - `ai/`: Intent parser, prompts system, and LLM orchestration wrappers.
  - `chat/`: REST API endpoints and `ChatService` coordinator.
  - `planner/`: Task planner schemas, prompts, and `Planner` engine.
  - `agent/`: Agent execution context, tasks executor, and the sequential execution loop.
  - `memory/`: Conversation memory tracker and pronoun reference resolver.
  - `tool_manager.py`: Directly dispatches intent requests to Phase 2 services.
- `tools/`: Modular tool layer (filesystem, notes, pdf, browser, system, productivity, gmail, calendar).
- `database/`: SQLite database storage (`echo_ai.db`).
- `logs/`: Structured JSON log outputs for requests, executions, retries, and errors.
- `tests/`: Extensive automated unit/integration/autonomy test suites.

---

## Architecture Diagram

```mermaid
flowchart TD
    User([User Request]) --> Router[POST /chat]
    Router --> ChatService[ChatService]
    ChatService --> Memory[MemoryManager]
    ChatService --> Planner[Planner]
    Planner -- generates Plan -- > Loop[AgentLoop]
    Loop --> Executor[Executor]
    Executor --> ToolMgr[ToolManager]
    ToolMgr -- execute step -- > Result[Execution Result]
    Result -- context passed -- > Executor
    Loop -- transient failure -- > Retry[RetryEngine]
    Loop -- duplicate note -- > Clarify[Clarification Registry]
    Loop -- success -- > ChatService
    ChatService --> Router
```

---

## Phase 4 Autonomous System

Echo AI Phase 4 transforms the operating system into an autonomous task-execution agent:

### 1. Task Planner
The Planner evaluates the user's natural language intent, accesses the Conversation Memory context to resolve any pronouns (like "it" or "the note"), and constructs a detailed, multi-step dependency-mapped execution `Plan`.

### 2. Executor & Agent Loop
The Loop runs plans sequentially. It dynamically injects execution results from earlier steps into subsequent steps (e.g. using `$step1_result` or `$step1_result.subfield` dot-notation) using a recursive `ExecutionContext` evaluator.

### 3. Memory
The Memory subsystem records references to recently managed files, notes, emails, and calendar events, summarizing them directly into the Planner prompt so that relative requests (e.g. "email it to John") resolve correctly.

### 4. Retry Engine
Automatically catches transient failures (socket errors, network dropouts, rate limits, server 502/503 statuses) and retries the tool execution up to `MAX_RETRIES` (default 3) using exponential backoff, skipping permanent syntax or parameter validation exceptions.

### 5. Clarification Engine
If a tool request identifies duplicate matching assets (such as multiple notes with the same name), the Loop pauses execution, registers the pending execution state under a stateful `session_id`, and returns the selection options. Responding with the index number or note ID resumes execution seamlessly.

### 6. Progress Events
Logs and returns structured execution status updates (e.g., `Planning...`, `Executing step 1/2...`, `Plan completed successfully.`).

---

## Configuration

Set up configuration settings by creating or updating `.env` in the project root:

```env
GROQ_API_KEY=gsk_your_actual_groq_api_key_here
MODEL_NAME=llama-3.3-70b-versatile
TEMPERATURE=0.0
MAX_TOKENS=1024

# Agent Autonomy Settings
PLANNER_MODEL=llama-3.3-70b-versatile
MAX_AGENT_STEPS=10
MAX_RETRIES=3
EXECUTION_TIMEOUT=30.0
ENABLE_MEMORY=True
ENABLE_PROGRESS=True
```

---

## Running the Server

Start the FastAPI development server:

```bash
$env:PYTHONPATH="echo-ai"; .venv\Scripts\uvicorn backend.main:app --reload
```

---

## Testing /chat Endpoint

The `/chat` endpoint accepts multi-step natural language queries, planning and execution events are run sequentially, and progress and results are returned.

### Multi-Step Example: Create a note and email it

**Request**:
`POST http://127.0.0.1:8000/chat`
```json
{
  "message": "Create a note called Shopping with content 'milk and eggs' then email it to john@example.com"
}
```

**Response**:
```json
{
  "success": true,
  "tool": "gmail",
  "action": "send",
  "result": {
    "recipient": "john@example.com",
    "subject": "Shopping",
    "body": "Note Content: milk and eggs"
  },
  "error": null,
  "requires_clarification": false,
  "message": null,
  "options": null,
  "progress_events": [
    "Analyzing query and formulating plan...",
    "Running step 1/2: Notes Tool: create...",
    "Running step 2/2: Gmail Tool: send...",
    "All planned steps completed successfully."
  ],
  "session_id": null
}
```

---

## Running the Test Suite

Run the full automated test suite containing 76 comprehensive test cases:

```bash
$env:PYTHONPATH="echo-ai"; .venv\Scripts\pytest.exe echo-ai
```
