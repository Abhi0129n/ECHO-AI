from fastapi import APIRouter, HTTPException, Depends
from typing import List
from tools.browser.service import BrowserService
from tools.browser.schemas import (
    SearchRequest,
    SearchResultItem,
    ReadPageRequest,
    ReadPageResponse,
    DownloadPDFRequest
)

router = APIRouter(prefix="/browser", tags=["browser"])

def get_browser_service() -> BrowserService:
    return BrowserService(base_dir=".")

@router.post("/search", response_model=List[SearchResultItem])
def google_search(request: SearchRequest, service: BrowserService = Depends(get_browser_service)):
    try:
        return service.google_search(request.query, request.max_results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/read", response_model=ReadPageResponse)
def read_page(request: ReadPageRequest, service: BrowserService = Depends(get_browser_service)):
    try:
        return service.read_page(request.url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/download-pdf")
def download_pdf(request: DownloadPDFRequest, service: BrowserService = Depends(get_browser_service)):
    try:
        local_path = service.download_pdf(request.url, request.output_filename)
        return {"status": "success", "file_path": local_path}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
