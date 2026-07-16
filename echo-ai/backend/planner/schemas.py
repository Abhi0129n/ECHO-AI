from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Any, Optional

VALID_TOOLS = {
    "file": {"find", "create_folder", "rename", "move", "copy", "delete", "open", "list"},
    "notes": {"create", "read", "update", "delete", "search"},
    "pdf": {"read", "search"},
    "browser": {"search", "read", "download_pdf"},
    "system": {"cpu", "memory", "disk", "battery", "processes", "apps", "open", "close"},
    "productivity": {"excel", "word", "powerpoint", "csv_read"},
    "gmail": {"unread", "search", "message", "send", "reply", "archive", "download_attachment", "delete"},
    "calendar": {"today", "search", "create", "update", "move", "delete", "free_slots"},
    "knowledge": {"search", "index_document", "delete_document", "list_documents", "reindex", "summarize_document"},
    "none": {"none"}
}

class Task(BaseModel):
    step: int = Field(..., description="The sequence step number of this task (1-indexed)")
    tool: str = Field(..., description="The tool to execute (e.g. 'file', 'notes', 'browser', 'pdf', 'system', 'productivity', 'gmail', 'calendar', 'none')")
    action: str = Field(..., description="The specific action to perform on the tool")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameters mapping for the tool action")
    dependencies: List[int] = Field(default_factory=list, description="List of step numbers this step depends on")

    @field_validator("tool")
    @classmethod
    def validate_tool_name(cls, v: str) -> str:
        tool_lower = v.lower()
        if tool_lower not in VALID_TOOLS:
            raise ValueError(f"Invalid tool: '{v}'. Must be one of {list(VALID_TOOLS.keys())}")
        return tool_lower

    @field_validator("action")
    @classmethod
    def validate_action_name(cls, v: str, info) -> str:
        # Get tool name from input values
        tool = info.data.get("tool")
        if not tool:
            return v.lower()
        tool_lower = tool.lower()
        action_lower = v.lower()
        
        valid_actions = VALID_TOOLS.get(tool_lower, set())
        if action_lower not in valid_actions:
            raise ValueError(f"Invalid action '{v}' for tool '{tool}'. Valid actions are: {list(valid_actions)}")
        return action_lower

class Plan(BaseModel):
    steps: List[Task] = Field(default_factory=list, description="Ordered list of execution tasks")

class ExecutionResult(BaseModel):
    step: int
    tool: str
    action: str
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None

class PlannerResponse(BaseModel):
    success: bool = Field(default=True)
    plan: Plan = Field(..., description="The generated plan steps")

class PlannerError(BaseModel):
    success: bool = Field(default=False)
    error: str = Field(..., description="Detailed description of planning error")
