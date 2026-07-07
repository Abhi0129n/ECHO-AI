import os
import shutil
from typing import List, Dict, Any

class FilesystemService:
    def __init__(self, base_dir: str = "."):
        self.base_dir = os.path.abspath(base_dir)

    def list_dir(self, path: str = "") -> List[Dict[str, Any]]:
        target_path = os.path.join(self.base_dir, path)
        if not os.path.exists(target_path):
            raise FileNotFoundError(f"Path {path} does not exist.")
        
        items = []
        for entry in os.scandir(target_path):
            items.append({
                "name": entry.name,
                "is_dir": entry.is_dir(),
                "size": entry.stat().st_size if entry.is_file() else None
            })
        return items

    def read_file(self, path: str) -> str:
        target_path = os.path.join(self.base_dir, path)
        with open(target_path, "r", encoding="utf-8") as f:
            return f.read()

    def write_file(self, path: str, content: str) -> None:
        target_path = os.path.join(self.base_dir, path)
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(content)
