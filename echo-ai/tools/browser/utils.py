import urllib.parse

def is_valid_url(url: str) -> bool:
    """Check if the provided string is a valid URL with http or https schema."""
    try:
        result = urllib.parse.urlparse(url)
        return result.scheme in ("http", "https") and bool(result.netloc)
    except ValueError:
        return False
