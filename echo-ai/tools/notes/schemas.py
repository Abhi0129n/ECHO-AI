from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class NoteBase(BaseModel):
    title: str = Field(..., description="The title of the note")
    content: str = Field(..., description="The markdown or text content of the note")
    tags: List[str] = Field(default_factory=list, description="Tags associated with the note")

class NoteCreate(NoteBase):
    pass

class NoteUpdate(BaseModel):
    title: Optional[str] = Field(None, description="Updated title of the note")
    content: Optional[str] = Field(None, description="Updated content of the note")
    tags: Optional[List[str]] = Field(None, description="Updated tags list")

class NoteResponse(BaseModel):
    id: int
    title: str
    content: str
    tags: List[str]
    created_at: str
    updated_at: str

    model_config = {
        "from_attributes": True
    }
