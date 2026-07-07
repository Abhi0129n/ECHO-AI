from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Any
from tools.excel.excel_models import WorkbookCreateRequest, SheetRequest, CellRequest, RowRequest, WorkbookResponse
from tools.excel.excel_service import ExcelService

router = APIRouter(prefix="/excel", tags=["excel"])
service = ExcelService()

@router.post("/create", response_model=WorkbookResponse)
def create_workbook(request: WorkbookCreateRequest):
    try:
        return service.create_workbook(request.path, request.sheets)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/open", response_model=WorkbookResponse)
def open_workbook(path: str):
    try:
        return service.open_workbook(path)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/write")
def write_cell(request: CellRequest):
    try:
        service.write_cell(request.path, request.sheet_name, request.cell, request.value)
        return {"status": "success"}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/read")
def read_cell(path: str, sheet_name: str, cell: str):
    try:
        value = service.read_cell(path, sheet_name, cell)
        return {"cell": cell, "value": value}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/append")
def append_row(request: RowRequest):
    try:
        service.append_row(request.path, request.sheet_name, request.values)
        return {"status": "success"}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/save")
def save_workbook(path: str):
    try:
        saved_path = service.save_workbook(path)
        return {"status": "success", "saved_path": saved_path}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
