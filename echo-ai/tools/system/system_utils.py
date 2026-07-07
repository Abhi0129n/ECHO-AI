import re
import os

def bytes_to_gb(b: int) -> float:
    """Converts bytes to Gigabytes with 2 decimal precision."""
    return round(b / (1024 ** 3), 2)

def format_percent(val: float) -> str:
    """Formats float usage percentage into string (e.g. 45.2%)."""
    return f"{round(val, 1)}%"

def validate_app(app_name: str) -> bool:
    """
    Validates if an app name or command is safe to execute.
    Prevents command injection characters.
    """
    if not app_name:
        return False
    # Allowed characters: alphanumeric, spaces, dots, dashes, underscores, and slashes for paths
    return bool(re.match(r'^[a-zA-Z0-9_\-\.\s\\/]+$', app_name))
