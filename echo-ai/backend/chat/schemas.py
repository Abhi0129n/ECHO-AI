from pydantic import BaseModel, Field
from typing import Any, Optional, List, Dict

class ChatRequest(BaseModel):
    message: str = Field(..., description="The user's query or instruction to Echo AI")
    session_id: Optional[str] = Field(default=None, description="Optional active agent session ID to resume clarification")

class ChatResponse(BaseModel):
    success: bool = Field(..., description="Whether the operation succeeded")
    tool: str = Field(..., description="The tool that was matched and run (or 'none')")
    action: str = Field(..., description="The action that was triggered on the tool (or 'none')")
    result: Optional[Any] = Field(default=None, description="The returned execution results from the tool")
    error: Optional[str] = Field(default=None, description="Detailed error description if success is False")
    requires_clarification: Optional[bool] = Field(default=None, description="Set to true if multiple matching notes exist")
    message: Optional[str] = Field(default=None, description="Clarification instructions for the user")
    options: Optional[List[Dict[str, Any]]] = Field(default=None, description="List of note options to select from")
    progress_events: Optional[List[str]] = Field(default=None, description="Structured progress events log of execution")
    session_id: Optional[str] = Field(default=None, description="Session ID to track execution context state")
