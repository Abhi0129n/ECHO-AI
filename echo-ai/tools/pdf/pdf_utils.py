import os
import re
from typing import List, Tuple

def clean_text(text: str) -> str:
    """Removes extra whitespaces and non-printable characters."""
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def normalize_text(text: str) -> str:
    """Converts to lowercase and removes punctuation for easier searching."""
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    return text.strip()

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

def file_validator(path: str) -> bool:
    """Validates that file exists and has .pdf extension."""
    if not os.path.exists(path):
        return False
    return path.lower().endswith('.pdf')
