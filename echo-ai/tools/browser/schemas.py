from pydantic import BaseModel, Field
from typing import List, Optional

class SearchRequest(BaseModel):
    query: str = Field(..., description="Query to search for")
    max_results: int = Field(default=10, description="Maximum number of search results to return")

class SearchResultItem(BaseModel):
    title: str
    url: str
    snippet: str

class ReadPageRequest(BaseModel):
    url: str = Field(..., description="URL of the webpage to read")

class PDFLinkItem(BaseModel):
    text: str
    url: str

class ReadPageResponse(BaseModel):
    url: str
    title: str
    visible_text: str
    pdf_links: List[PDFLinkItem]

class DownloadPDFRequest(BaseModel):
    url: str = Field(..., description="Direct URL of the PDF to download")
    output_filename: Optional[str] = Field(None, description="Optional custom filename for the downloaded PDF")
