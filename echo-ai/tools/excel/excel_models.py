from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class WorkbookCreateRequest(BaseModel):
    path: str
    sheets: Optional[List[str]] = ["Sheet1"]

class SheetRequest(BaseModel):
    path: str
    sheet_name: str
    new_name: Optional[str] = None

class CellRequest(BaseModel):
    path: str
    sheet_name: str
    cell: str
    value: Optional[str] = None

class RowRequest(BaseModel):
    path: str
    sheet_name: str
    values: List[Any]

class WorkbookResponse(BaseModel):
    path: str
    sheets: List[str]
    active_sheet: str
