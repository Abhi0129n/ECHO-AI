import os

def is_safe_path(base_dir: str, path: str) -> bool:
    """Ensure path is within base directory."""
    resolved_base = os.path.abspath(base_dir)
    resolved_target = os.path.abspath(os.path.join(base_dir, path))
    return resolved_target.startswith(resolved_base)
