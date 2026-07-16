from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class IndexRequest(BaseModel):
    file_path: str = Field(..., description="Absolute path of the document file to index")

class DeleteRequest(BaseModel):
    file_path: str = Field(..., description="Absolute path of the document file to delete")

class SearchRequest(BaseModel):
    query: str = Field(..., description="Search query string")
    file_path_filter: Optional[str] = Field(default=None, description="Optional path to restrict search context")
    file_type_filter: Optional[str] = Field(default=None, description="Optional document type filter")

class Citation(BaseModel):
    filename: str
    file_path: str
    page_number: int
    chunk_number: int
    similarity_score: float

class SearchResponse(BaseModel):
    answer: str = Field(..., description="RAG generated response answer")
    citations: List[Citation] = Field(default_factory=list, description="Citations and document sources list")
    latency_ms: float

class SummarizeRequest(BaseModel):
    file_path: str = Field(..., description="Absolute path of the document file to summarize")
