from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any
from tools.browser.browser_models import WebsiteContent, WebsiteRequest
from tools.browser.browser_service import BrowserService

router = APIRouter(prefix="/browser", tags=["browser"])
service = BrowserService()

@router.get("/search", response_model=List[Dict[str, Any]])
def google_search(q: str, max_results: int = 10):
    try:
        return service.google_search(q, max_results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/read", response_model=WebsiteContent)
def read_page(url: str):
    try:
        return service.read_page(url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/download")
def download_pdf(url: str, output_path: str = "uploads/downloaded.pdf"):
    try:
        path = service.download_pdf(url, output_path)
        return {"status": "success", "file_path": path}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
