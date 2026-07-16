import os

def is_safe_path(base_dir: str, path: str) -> bool:
    """
    Ensure the path is safe and stays within the workspace boundary.
    Prevents directory traversal (e.g. using '../../') out of the workspace.
    """
    resolved_base = os.path.abspath(base_dir)
    # Join base directory with target path, then get absolute path
    resolved_target = os.path.abspath(os.path.join(resolved_base, path))
    return resolved_target.startswith(resolved_base)
