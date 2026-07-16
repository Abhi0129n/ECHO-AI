import re
import os
import base64
from typing import Optional, Any
from tools.filesystem.utils import is_safe_path

# Scopes required for the application
SCOPES = [
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.send'
]

def extract_email(sender_string: str) -> str:
    """Extracts email address from strings like 'Sender Name <sender@example.com>'."""
    if not sender_string:
        return ""
    match = re.search(r'<([^>]+)>', sender_string)
    if match:
        return match.group(1).strip()
    return sender_string.strip()

def format_subject(subject: str) -> str:
    """Prefixes subject with 'Re: ' if not already present."""
    if not subject:
        return "Re: (no subject)"
    if not subject.lower().startswith("re:"):
        return f"Re: {subject}"
    return subject

def save_attachment(data_base64: str, filename: str, base_dir: str = ".") -> str:
    """Decodes base64 attachment data and writes to the uploads folder securely."""
    uploads_dir = os.path.abspath(os.path.join(base_dir, "echo-ai", "uploads", "attachments"))
    os.makedirs(uploads_dir, exist_ok=True)
    
    file_path = os.path.join(uploads_dir, filename)
    if not is_safe_path(base_dir, os.path.relpath(file_path, base_dir)):
         raise PermissionError("Access denied: path is outside the workspace boundary")
         
    # Base64url decode
    decoded_data = base64.urlsafe_b64decode(data_base64)
    with open(file_path, "wb") as f:
        f.write(decoded_data)
        
    return os.path.relpath(file_path, base_dir)
