import os
from tools.filesystem.utils import is_safe_path

def resolve_and_verify_path(base_dir: str, path: str, expected_exts: list) -> str:
    """Ensure the path is safe within workspace and ends with an allowed extension."""
    if not is_safe_path(base_dir, path):
        raise PermissionError("Access denied: path is outside the workspace boundary")
        
    abs_path = os.path.abspath(os.path.join(base_dir, path))
    ext = os.path.splitext(abs_path)[1].lower()
    if ext not in expected_exts:
        raise ValueError(f"Invalid file extension. Expected one of: {expected_exts}")
        
    return abs_path
