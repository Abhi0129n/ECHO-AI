from fastapi import APIRouter, HTTPException, Depends
from tools.pdf.service import PDFService
from tools.pdf.schemas import (
    PDFReadRequest,
    PDFReadResponse,
    PDFSearchRequest,
    PDFSearchResponse
)

router = APIRouter(prefix="/pdf", tags=["pdf"])

def get_pdf_service() -> PDFService:
    return PDFService(base_dir=".")

@router.post("/read", response_model=PDFReadResponse)
def read_pdf(request: PDFReadRequest, service: PDFService = Depends(get_pdf_service)):
    try:
        return service.read_pdf(request.path, request.page_range)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search", response_model=PDFSearchResponse)
def search_pdf(request: PDFSearchRequest, service: PDFService = Depends(get_pdf_service)):
    try:
        return service.search_pdf(request.path, request.query)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
