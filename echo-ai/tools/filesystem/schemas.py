from pydantic import BaseModel, Field
from typing import Optional, List

class FileItem(BaseModel):
    name: str
    is_dir: bool
    size: Optional[int] = None
    path: str

class FindFileRequest(BaseModel):
    path: str = Field(default="", description="Base path to start searching from")
    query: str = Field(..., description="Query string to search for in filenames")
    recursive: bool = Field(default=True, description="Whether to search recursively")

class CreateFolderRequest(BaseModel):
    path: str = Field(..., description="Path of the folder to create")

class RenameFileRequest(BaseModel):
    path: str = Field(..., description="Path of the file or folder to rename")
    new_name: str = Field(..., description="New name for the file or folder")

class MoveFileRequest(BaseModel):
    src_path: str = Field(..., description="Source path of the file or folder")
    dest_path: str = Field(..., description="Destination path (including new filename or parent directory)")

class CopyFileRequest(BaseModel):
    src_path: str = Field(..., description="Source path of the file or folder")
    dest_path: str = Field(..., description="Destination path to copy to")

class DeleteFileRequest(BaseModel):
    path: str = Field(..., description="Path of the file or folder to delete")

class OpenFileRequest(BaseModel):
    path: str = Field(..., description="Path of the file to open using OS default app")
