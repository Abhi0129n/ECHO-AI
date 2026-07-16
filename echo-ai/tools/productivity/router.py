from fastapi import APIRouter, HTTPException, Depends
from typing import List
from tools.productivity.service import ProductivityService
from tools.productivity.schemas import (
    CreateExcelRequest,
    CreateWordRequest,
    CreatePPTRequest,
    ReadCSVRequest
)

router = APIRouter(prefix="/productivity", tags=["productivity"])

def get_productivity_service() -> ProductivityService:
    return ProductivityService(base_dir=".")

@router.post("/excel")
def create_excel(request: CreateExcelRequest, service: ProductivityService = Depends(get_productivity_service)):
    try:
        file_path = service.create_excel(request.path, request.data)
        return {"status": "success", "file_path": file_path}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/word")
def create_word(request: CreateWordRequest, service: ProductivityService = Depends(get_productivity_service)):
    try:
        file_path = service.create_word(request.path, request.title, request.content)
        return {"status": "success", "file_path": file_path}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/powerpoint")
def create_ppt(request: CreatePPTRequest, service: ProductivityService = Depends(get_productivity_service)):
    try:
        file_path = service.create_ppt(request.path, request.title, request.subtitle, request.slides)
        return {"status": "success", "file_path": file_path}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/csv/read", response_model=List[List[str]])
def read_csv(request: ReadCSVRequest, service: ProductivityService = Depends(get_productivity_service)):
    try:
        return service.read_csv(request.path)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
