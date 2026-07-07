from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class NoteBase(BaseModel):
    title: str
    content: str
    tags: List[str] = Field(default_factory=list)

class NoteCreate(NoteBase):
    pass

class NoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = None

class Note(NoteBase):
    id: str
    created_at: str
    updated_at: str
