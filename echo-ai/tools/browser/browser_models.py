from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Dict, Any

class WebsiteRequest(BaseModel):
    url: str

class SearchRequest(BaseModel):
    query: str
    max_results: Optional[int] = 10

class LinkItem(BaseModel):
    text: str
    url: str

class WebsiteContent(BaseModel):
    url: str
    title: str
    html_content: str
    text_content: str
    links: List[LinkItem] = []
    images: List[str] = []
