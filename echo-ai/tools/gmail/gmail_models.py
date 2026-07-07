from pydantic import BaseModel, EmailStr
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
    recipient: str
    subject: str
    body: str
    attachments: Optional[List[str]] = []

class ReplyRequest(BaseModel):
    body: str
    attachments: Optional[List[str]] = []

class SearchRequest(BaseModel):
    query: str
    max_results: Optional[int] = 20
