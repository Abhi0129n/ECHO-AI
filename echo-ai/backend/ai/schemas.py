from pydantic import BaseModel, Field
from typing import Dict, Any

class IntentSchema(BaseModel):
    tool: str = Field(..., description="The name of the tool to invoke (e.g. 'file', 'notes', 'browser', 'pdf', 'system', 'productivity', 'gmail', 'calendar')")
    action: str = Field(..., description="The specific action to perform on the tool")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameters matching the action signature")
