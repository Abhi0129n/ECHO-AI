import os
import fitz  # PyMuPDF
from typing import List, Dict, Optional
from tools.pdf.schemas import (
    PDFPageDetail,
    PDFReadResponse,
    PDFSearchResultItem,
    PDFSearchResponse
)
from tools.pdf.utils import file_validator, page_range_validator

class PDFService:
    def __init__(self, base_dir: str = "."):
        self.base_dir = os.path.abspath(base_dir)

    def read_pdf(self, path: str, page_range: Optional[str] = None) -> PDFReadResponse:
        abs_path = file_validator(self.base_dir, path)
        
        doc = fitz.open(abs_path)
        try:
            page_count = len(doc)
            metadata = {
                "author": doc.metadata.get("author"),
                "creator": doc.metadata.get("creator"),
                "producer": doc.metadata.get("producer"),
                "subject": doc.metadata.get("subject"),
                "title": doc.metadata.get("title")
            }
            
            pages_to_read = page_range_validator(page_range, page_count)
            pages = []
            for p_idx in pages_to_read:
                page = doc[p_idx]
                pages.append(PDFPageDetail(
                    page_number=p_idx + 1,
                    text=page.get_text()
                ))
                
            return PDFReadResponse(
                path=path,
                page_count=page_count,
                metadata=metadata,
                pages=pages
            )
        finally:
            doc.close()

    def search_pdf(self, path: str, query: str) -> PDFSearchResponse:
        abs_path = file_validator(self.base_dir, path)
        
        doc = fitz.open(abs_path)
        try:
            results = []
            query_lower = query.lower()
            for p_idx in range(len(doc)):
                page = doc[p_idx]
                page_text = page.get_text()
                
                text_lower = page_text.lower()
                idx = text_lower.find(query_lower)
                if idx != -1:
                    start = max(0, idx - 40)
                    end = min(len(page_text), idx + len(query) + 80)
                    snippet = page_text[start:end].replace('\n', ' ')
                    results.append(PDFSearchResultItem(
                        page_number=p_idx + 1,
                        snippet=f"...{snippet}..."
                    ))
            return PDFSearchResponse(
                path=path,
                query=query,
                results=results
            )
        finally:
            doc.close()
