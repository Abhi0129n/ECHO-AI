import os
import time
import json
import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

from backend.ai.llm import LLMService
from backend.planner.planner import Planner
from backend.planner.schemas import Plan, Task
from backend.agent.context import ExecutionContext
from backend.agent.executor import Executor
from backend.agent.loop import AgentLoop
from backend.memory.conversation_memory import ConversationMemory
from backend.chat.schemas import ChatResponse
from tools.notes.service import NotesService

LOGS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "logs"))
AI_LOG_FILE = os.path.join(LOGS_DIR, "ai_chat.log")

class ChatService:
    # Class-level state persistence across stateless REST requests
    memory = ConversationMemory()
    sessions: Dict[str, Dict[str, Any]] = {}

    def __init__(self, base_dir: str = ".", notes_service: Optional[NotesService] = None):
        self.base_dir = os.path.abspath(base_dir)
        self.llm_service = LLMService()
        self.planner = Planner(llm_service=self.llm_service)
        
        # Load environment variables with proper fallback defaults
        self.max_steps = int(os.getenv("MAX_AGENT_STEPS", "10"))
        self.max_retries = int(os.getenv("MAX_RETRIES", "3"))
        self.timeout = float(os.getenv("EXECUTION_TIMEOUT", "30.0"))
        self.enable_memory = os.getenv("ENABLE_MEMORY", "True").lower() == "true"
        self.enable_progress = os.getenv("ENABLE_PROGRESS", "True").lower() == "true"
        
        # Construct agent components
        self.tool_manager = self.planner.llm_service.client = None
        from backend.tool_manager import ToolManager
        self.tool_manager = ToolManager(base_dir=self.base_dir, notes_service=notes_service)
        self.executor = Executor(tool_manager=self.tool_manager, max_retries=self.max_retries)

    def handle_chat_message(self, message: str, session_id: Optional[str] = None) -> ChatResponse:
        """
        Coordinates Chat query processing. Executes plans, handles context sharing,
        transient retries, clarification tracking, and updates conversation memory.
        """
        start_total = time.time()
        progress_log: List[str] = []
        
        def on_progress(event_msg: str):
            if self.enable_progress:
                progress_log.append(event_msg)

        # Execution tracking states
        tool_name = "none"
        action_name = "none"
        success = True
        error_msg = None
        result = None
        requires_clarification = False
        clarification_message = None
        options = None
        new_session_id = session_id
        
        try:
            # Case A: Resuming a pending clarification session
            if session_id and session_id in ChatService.sessions:
                session = ChatService.sessions[session_id]
                on_progress(f"Resuming active session '{session_id}' based on user selection...")
                
                # Parse choice from user message (ID or option number)
                clean_msg = "".join([c for c in message if c.isdigit()])
                selected_option = None
                
                if clean_msg:
                    choice_num = int(clean_msg)
                    opts = session["options"]
                    # 1. Try mapping as direct database note ID first (to prevent ID vs Index conflict)
                    for opt in opts:
                        if opt.get("id") == choice_num:
                            selected_option = opt
                            break
                    
                    # 2. Fallback to mapping as 1-indexed choice number
                    if not selected_option and 1 <= choice_num <= len(opts):
                        selected_option = opts[choice_num - 1]
                                
                if not selected_option:
                    # Return choices again if selection is invalid
                    on_progress("Invalid choice received. Re-prompting user...")
                    return ChatResponse(
                        success=False,
                        tool="notes",
                        action="read",
                        requires_clarification=True,
                        message=session["message"],
                        options=session["options"],
                        session_id=session_id,
                        progress_events=progress_log
                    )
                
                # Retrieve execution states
                plan = session["plan"]
                pending_step_idx = session["pending_step_idx"]
                context = session["context"]
                
                # Override parameters to utilize resolved note ID directly and clear title resolution triggers
                task = plan.steps[pending_step_idx]
                task.parameters["id"] = selected_option["id"]
                if "title" in task.parameters:
                    del task.parameters["title"]
                
                # Clean up session registry
                del ChatService.sessions[session_id]
                new_session_id = None
                
                # Resume execution
                loop = AgentLoop(
                    executor=self.executor,
                    max_steps=self.max_steps,
                    timeout=self.timeout,
                    progress_callback=on_progress
                )
                loop_result = loop.run(plan, start_step_idx=pending_step_idx, context=context)

            # Case B: Initiating a new execution flow
            else:
                on_progress("Analyzing query and formulating plan...")
                memory_ctx = ChatService.memory.to_prompt_context() if self.enable_memory else ""
                
                # 1. Generate multi-step execution plan
                plan = self.planner.generate_plan(message, memory_context=memory_ctx)
                context = ExecutionContext()
                
                # 2. Run plan steps via Agent Loop
                loop = AgentLoop(
                    executor=self.executor,
                    max_steps=self.max_steps,
                    timeout=self.timeout,
                    progress_callback=on_progress
                )
                loop_result = loop.run(plan, context=context)

            # Process Loop Outcomes
            if loop_result["status"] == "clarification":
                # Duplicate resources found - pause and request user selection
                requires_clarification = True
                clarification_message = loop_result["message"]
                options = loop_result["options"]
                success = False
                error_msg = clarification_message
                
                # Store context state to support resume
                new_session_id = session_id or f"session_{uuid.uuid4().hex[:8]}"
                ChatService.sessions[new_session_id] = {
                    "plan": loop_result["plan"],
                    "pending_step_idx": loop_result["pending_step_idx"],
                    "context": loop_result["context"],
                    "options": options,
                    "message": clarification_message
                }
                
                if plan.steps:
                    current_task = plan.steps[loop_result["pending_step_idx"]]
                    tool_name = current_task.tool
                    action_name = current_task.action
            else:
                # Successfully completed plan
                result = loop_result["result"]
                context = loop_result["context"]
                
                if plan.steps:
                    last_task = plan.steps[-1]
                    tool_name = last_task.tool
                    action_name = last_task.action
                    
                    # Update Conversation Memory with resolved outputs of executed steps
                    for task in plan.steps:
                        step_output = context.outputs.get(task.step)
                        resolved_params = context.resolve_parameters(task.parameters)
                        ChatService.memory.update(task.tool, task.action, resolved_params, step_output)

        except Exception as e:
            success = False
            error_msg = str(e)
            if 'plan' in locals() and plan.steps:
                last_task = plan.steps[-1]
                tool_name = last_task.tool
                action_name = last_task.action

        total_time_ms = round((time.time() - start_total) * 1000, 2)
        
        # Logging structured metrics
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_message": message,
            "session_id": new_session_id,
            "chosen_tool": tool_name,
            "chosen_action": action_name,
            "total_execution_time_ms": total_time_ms,
            "success": success,
            "error": error_msg,
            "requires_clarification": requires_clarification,
            "progress": progress_log
        }
        
        os.makedirs(LOGS_DIR, exist_ok=True)
        try:
            with open(AI_LOG_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as log_err:
            print(f"Failed to write AI chat log: {str(log_err)}")
            
        return ChatResponse(
            success=success,
            tool=tool_name,
            action=action_name,
            result=result,
            error=error_msg,
            requires_clarification=requires_clarification,
            message=clarification_message,
            options=options,
            progress_events=progress_log,
            session_id=new_session_id
        )
