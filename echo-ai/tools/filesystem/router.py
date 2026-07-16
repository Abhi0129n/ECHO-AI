from fastapi import APIRouter, HTTPException, Depends
from typing import List
from tools.filesystem.service import FilesystemService
from tools.filesystem.schemas import (
    FileItem,
    FindFileRequest,
    CreateFolderRequest,
    RenameFileRequest,
    MoveFileRequest,
    CopyFileRequest,
    DeleteFileRequest,
    OpenFileRequest
)

router = APIRouter(prefix="/file", tags=["file"])

# Dependency to get FilesystemService (configured with workspace root as base_dir)
def get_fs_service() -> FilesystemService:
    return FilesystemService(base_dir=".")

@router.get("/list", response_model=List[FileItem])
def list_files(path: str = "", service: FilesystemService = Depends(get_fs_service)):
    try:
        return service.list_dir(path)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except NotADirectoryError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/find", response_model=List[FileItem])
def find_files(request: FindFileRequest, service: FilesystemService = Depends(get_fs_service)):
    try:
        return service.find_files(request.path, request.query, request.recursive)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create-folder")
def create_folder(request: CreateFolderRequest, service: FilesystemService = Depends(get_fs_service)):
    try:
        created_path = service.create_folder(request.path)
        return {"status": "success", "path": created_path}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/rename")
def rename_file(request: RenameFileRequest, service: FilesystemService = Depends(get_fs_service)):
    try:
        new_path = service.rename(request.path, request.new_name)
        return {"status": "success", "old_path": request.path, "new_path": new_path}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except FileExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/move")
def move_file(request: MoveFileRequest, service: FilesystemService = Depends(get_fs_service)):
    try:
        service.move(request.src_path, request.dest_path)
        return {"status": "success", "src_path": request.src_path, "dest_path": request.dest_path}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/copy")
def copy_file(request: CopyFileRequest, service: FilesystemService = Depends(get_fs_service)):
    try:
        service.copy(request.src_path, request.dest_path)
        return {"status": "success", "src_path": request.src_path, "dest_path": request.dest_path}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/delete")
def delete_file(request: DeleteFileRequest, service: FilesystemService = Depends(get_fs_service)):
    try:
        service.delete(request.path)
        return {"status": "success", "deleted_path": request.path}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/open")
def open_file(request: OpenFileRequest, service: FilesystemService = Depends(get_fs_service)):
    try:
        service.open_file(request.path)
        return {"status": "success", "message": f"Opened file '{request.path}' successfully"}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except IsADirectoryError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
