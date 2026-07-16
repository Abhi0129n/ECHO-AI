import re

def bytes_to_gb(b: int) -> float:
    """Converts bytes to Gigabytes with 2 decimal precision."""
    return round(b / (1024 ** 3), 2)

def validate_app(app_name: str) -> bool:
    """
    Validates if an app name or command is safe to execute.
    Prevents command injection characters.
    """
    if not app_name:
        return False
    # Allowed characters: alphanumeric, spaces, dots, dashes, underscores, slashes, and colons (for Windows drive letters)
    return bool(re.match(r'^[a-zA-Z0-9_\-\.\s\\/:]+$', app_name))
