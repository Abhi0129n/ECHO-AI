import os
from typing import List
from tools.filesystem.utils import is_safe_path

def page_range_validator(page_range: str, total_pages: int) -> List[int]:
    """
    Parses page range strings like '1-3, 5, 7-9' and returns a list of 0-indexed page numbers.
    """
    pages = set()
    if not page_range:
        return list(range(total_pages))
    
    parts = page_range.split(',')
    for part in parts:
        part = part.strip()
        if '-' in part:
            try:
                start_str, end_str = part.split('-')
                start = int(start_str.strip())
                end = int(end_str.strip())
                # Clamp within boundaries
                start = max(1, min(start, total_pages))
                end = max(1, min(end, total_pages))
                for p in range(min(start, end), max(start, end) + 1):
                    pages.add(p - 1)
            except ValueError:
                continue
        else:
            try:
                p = int(part)
                if 1 <= p <= total_pages:
                    pages.add(p - 1)
            except ValueError:
                continue
                
    return sorted(list(pages))

def file_validator(base_dir: str, path: str) -> str:
    """Validates path safety, file existence, and PDF extension, returning absolute path."""
    if not is_safe_path(base_dir, path):
        raise PermissionError("Access denied: path is outside the workspace boundary")
    abs_path = os.path.abspath(os.path.join(base_dir, path))
    if not os.path.exists(abs_path):
        raise FileNotFoundError(f"PDF file '{path}' does not exist")
    if not path.lower().endswith('.pdf'):
        raise ValueError(f"File '{path}' is not a PDF")
    return abs_path
