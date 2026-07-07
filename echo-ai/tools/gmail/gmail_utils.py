import re
import os
import base64

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

def clean_html(html_content: str) -> str:
    """Removes HTML tags to extract raw text content."""
    if not html_content:
        return ""
    # Strip HTML tags
    clean = re.sub(r'<[^>]+>', ' ', html_content)
    # Normalize whitespaces
    clean = re.sub(r'\s+', ' ', clean)
    return clean.strip()

def save_attachment(data_base64: str, filename: str, output_dir: str = "uploads/attachments") -> str:
    """Decodes base64 attachment data and writes to the outputs folder."""
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, filename)
    
    # Base64url decode
    decoded_data = base64.urlsafe_b64decode(data_base64)
    with open(file_path, "wb") as f:
        f.write(decoded_data)
        
    return file_path
