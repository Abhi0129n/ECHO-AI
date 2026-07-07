from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from tools.pdf.pdf_models import PDFMetadata, PDFTextResponse, PDFSearchResult, PDFPage
from tools.pdf.pdf_service import PDFService

router = APIRouter(prefix="/pdf", tags=["pdf"])
service = PDFService()

@router.get("/pages", response_model=PDFMetadata)
def count_pages(path: str):
    try:
        return service.extract_metadata(path)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/text", response_model=PDFTextResponse)
def extract_text(path: str, page_range: Optional[str] = None):
    try:
        pages = service.extract_text(path, page_range)
        return PDFTextResponse(
            path=path,
            pages=pages,
            total_pages=service.count_pages(path)
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search", response_model=List[PDFSearchResult])
def search_text(path: str, query: str):
    try:
        return service.search_text(path, query)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/split", response_model=List[str])
def split_pdf(path: str, page_ranges: str, output_dir: str = "outputs"):
    try:
        return service.split_pdf(path, page_ranges, output_dir)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/merge")
def merge_pdf(paths: List[str] = Query(...), output_path: str = "outputs/merged.pdf"):
    try:
        merged_path = service.merge_pdf(paths, output_path)
        return {"status": "success", "merged_path": merged_path}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
