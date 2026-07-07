from pydantic import BaseModel
from typing import Optional, Dict, Any, List

class PDFOpenRequest(BaseModel):
    path: str

class PDFMetadata(BaseModel):
    author: Optional[str] = None
    creator: Optional[str] = None
    producer: Optional[str] = None
    subject: Optional[str] = None
    title: Optional[str] = None
    pages: int

class PDFPage(BaseModel):
    page_number: int
    text: str

class PDFTextResponse(BaseModel):
    path: str
    pages: List[PDFPage]
    total_pages: int

class PDFSearchResult(BaseModel):
    page_number: int
    matched_text: str
    index: int
