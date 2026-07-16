from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class Attachment(BaseModel):
    id: str
    filename: str
    mime_type: str
    size_bytes: int

class EmailSummary(BaseModel):
    id: str
    thread_id: str
    sender: str
    subject: str
    snippet: str
    received_at: str
    is_unread: bool

class EmailMessage(BaseModel):
    id: str
    thread_id: str
    sender: str
    recipient: str
    subject: str
    body_text: str
    body_html: Optional[str] = None
    received_at: str
    labels: List[str]
    attachments: List[Attachment] = []

class EmailRequest(BaseModel):
    recipient: str = Field(..., description="Recipient email address")
    subject: str = Field(..., description="Email subject")
    body: str = Field(..., description="Email body (plain text)")
    attachments: Optional[List[str]] = Field(default_factory=list, description="List of local file paths to attach")

class ReplyRequest(BaseModel):
    body: str = Field(..., description="Reply body text")
    attachments: Optional[List[str]] = Field(default_factory=list, description="List of local file paths to attach")
