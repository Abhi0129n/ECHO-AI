import re
from typing import Union, List, Dict, Any

def column_converter(col: Union[int, str]) -> Union[str, int]:
    """
    Converts a column letter (e.g. 'A') to a 1-based index (e.g. 1) or vice versa.
    """
    if isinstance(col, int):
        # Index to Letter
        result = []
        while col > 0:
            col, remainder = divmod(col - 1, 26)
            result.append(chr(remainder + 65))
        return "".join(reversed(result))
    elif isinstance(col, str):
        # Letter to Index
        col = col.upper()
        index = 0
        for char in col:
            index = index * 26 + (ord(char) - 64)
        return index
    raise ValueError("Invalid type for column conversion")

def validate_sheet(sheet_name: str) -> bool:
    """Validates if excel sheet name has valid characters and length."""
    if not sheet_name or len(sheet_name) > 31:
        return False
    invalid_chars = [':', '\\', '/', '?', '*', '[', ']']
    return not any(char in sheet_name for char in invalid_chars)

def validate_cell(cell_ref: str) -> bool:
    """Checks if cell reference format is correct (e.g. 'A1', 'B20')."""
    return bool(re.match(r'^[A-Z]+[1-9][0-9]*$', cell_ref, re.IGNORECASE))

def format_table(headers: List[str], rows: List[List[Any]]) -> List[Dict[str, Any]]:
    """Formats raw headers and rows into structured dictionaries."""
    formatted = []
    for row in rows:
        item = {}
        for idx, header in enumerate(headers):
            item[header] = row[idx] if idx < len(row) else None
        formatted.append(item)
    return formatted
