from fastapi import APIRouter, HTTPException
from typing import List
from tools.filesystem.filesystem_service import FilesystemService
from tools.filesystem.filesystem_models import FileItem, FileWriteRequest
from tools.filesystem.filesystem_utils import is_safe_path

router = APIRouter(prefix="/filesystem", tags=["filesystem"])
service = FilesystemService(base_dir=".")

@router.get("/list", response_model=List[FileItem])
def list_files(path: str = ""):
    if not is_safe_path(".", path):
        raise HTTPException(status_code=400, detail="Access denied: outside workspace")
    try:
        return service.list_dir(path)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/read")
def read_file(path: str):
    if not is_safe_path(".", path):
        raise HTTPException(status_code=400, detail="Access denied: outside workspace")
    try:
        return {"content": service.read_file(path)}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/write")
def write_file(request: FileWriteRequest):
    if not is_safe_path(".", request.path):
        raise HTTPException(status_code=400, detail="Access denied: outside workspace")
    try:
        service.write_file(request.path, request.content)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
