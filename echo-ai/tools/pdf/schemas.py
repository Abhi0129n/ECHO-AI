from pydantic import BaseModel, Field
from typing import Optional, List, Dict

class PDFReadRequest(BaseModel):
    path: str = Field(..., description="Path to the PDF file")
    page_range: Optional[str] = Field(None, description="Optional page range (e.g. '1-3, 5')")

class PDFPageDetail(BaseModel):
    page_number: int
    text: str

class PDFReadResponse(BaseModel):
    path: str
    page_count: int
    metadata: Dict[str, Optional[str]]
    pages: List[PDFPageDetail]

class PDFSearchRequest(BaseModel):
    path: str = Field(..., description="Path to the PDF file")
    query: str = Field(..., description="Keyword query to search for")

class PDFSearchResultItem(BaseModel):
    page_number: int
    snippet: str

class PDFSearchResponse(BaseModel):
    path: str
    query: str
    results: List[PDFSearchResultItem]
