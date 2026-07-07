from pydantic import BaseModel
from typing import Optional, List

class FileItem(BaseModel):
    name: str
    is_dir: bool
    size: Optional[int] = None

class FileWriteRequest(BaseModel):
    path: str
    content: str
