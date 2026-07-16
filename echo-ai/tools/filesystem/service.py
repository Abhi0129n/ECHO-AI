import os
import shutil
import subprocess
import sys
from typing import List, Optional
from tools.filesystem.schemas import FileItem
from tools.filesystem.utils import is_safe_path

class FilesystemService:
    def __init__(self, base_dir: str = "."):
        self.base_dir = os.path.abspath(base_dir)

    def _resolve_and_verify(self, path: str) -> str:
        """Helper to resolve a path and verify it lies within base_dir."""
        if not is_safe_path(self.base_dir, path):
            raise PermissionError("Access denied: path is outside the workspace boundary")
        return os.path.abspath(os.path.join(self.base_dir, path))

    def list_dir(self, path: str = "") -> List[FileItem]:
        target_path = self._resolve_and_verify(path)
        if not os.path.exists(target_path):
            raise FileNotFoundError(f"Path '{path}' does not exist.")
        if not os.path.isdir(target_path):
            raise NotADirectoryError(f"Path '{path}' is not a directory.")
        
        items = []
        for entry in os.scandir(target_path):
            # Calculate path relative to self.base_dir to return clean relative paths
            rel_path = os.path.relpath(entry.path, self.base_dir)
            items.append(FileItem(
                name=entry.name,
                is_dir=entry.is_dir(),
                size=entry.stat().st_size if entry.is_file() else None,
                path=rel_path
            ))
        return items

    def find_files(self, path: str, query: str, recursive: bool = True) -> List[FileItem]:
        target_path = self._resolve_and_verify(path)
        if not os.path.exists(target_path):
            raise FileNotFoundError(f"Starting path '{path}' does not exist.")
        
        items = []
        # Normalise query for case-insensitive matching
        query_lower = query.lower()

        if recursive:
            for root, dirs, files in os.walk(target_path):
                # Verify safety of root in each walk iteration
                if not is_safe_path(self.base_dir, os.path.relpath(root, self.base_dir)):
                    continue
                
                # Check matching directories
                for d in dirs:
                    if query_lower in d.lower():
                        d_path = os.path.join(root, d)
                        rel_path = os.path.relpath(d_path, self.base_dir)
                        items.append(FileItem(
                            name=d,
                            is_dir=True,
                            size=None,
                            path=rel_path
                        ))
                
                # Check matching files
                for f in files:
                    if query_lower in f.lower():
                        f_path = os.path.join(root, f)
                        rel_path = os.path.relpath(f_path, self.base_dir)
                        try:
                            size = os.path.getsize(f_path)
                        except OSError:
                            size = None
                        items.append(FileItem(
                            name=f,
                            is_dir=False,
                            size=size,
                            path=rel_path
                        ))
        else:
            # Non-recursive, list and filter
            for entry in os.scandir(target_path):
                if query_lower in entry.name.lower():
                    rel_path = os.path.relpath(entry.path, self.base_dir)
                    items.append(FileItem(
                        name=entry.name,
                        is_dir=entry.is_dir(),
                        size=entry.stat().st_size if entry.is_file() else None,
                        path=rel_path
                    ))
        return items

    def create_folder(self, path: str) -> str:
        target_path = self._resolve_and_verify(path)
        os.makedirs(target_path, exist_ok=True)
        return os.path.relpath(target_path, self.base_dir)

    def rename(self, path: str, new_name: str) -> str:
        target_path = self._resolve_and_verify(path)
        if not os.path.exists(target_path):
            raise FileNotFoundError(f"Path '{path}' does not exist.")
        
        # New target sits in the same directory but with new_name
        parent_dir = os.path.dirname(target_path)
        new_target_path = os.path.join(parent_dir, new_name)
        
        # Verify new target safety
        if not is_safe_path(self.base_dir, os.path.relpath(new_target_path, self.base_dir)):
            raise PermissionError("Access denied: rename destination path is outside workspace")
            
        if os.path.exists(new_target_path):
            raise FileExistsError(f"Destination '{new_name}' already exists in parent folder.")
            
        os.rename(target_path, new_target_path)
        self._trigger_auto_index(new_target_path, "rename", old_path=target_path)
        return os.path.relpath(new_target_path, self.base_dir)

    def move(self, src_path: str, dest_path: str) -> None:
        target_src = self._resolve_and_verify(src_path)
        target_dest = self._resolve_and_verify(dest_path)
        
        if not os.path.exists(target_src):
            raise FileNotFoundError(f"Source path '{src_path}' does not exist.")
            
        # Resolve target destination full path
        resolved_dest = target_dest
        if os.path.isdir(target_dest):
            resolved_dest = os.path.join(target_dest, os.path.basename(target_src))

        shutil.move(target_src, target_dest)
        self._trigger_auto_index(resolved_dest, "rename", old_path=target_src)

    def copy(self, src_path: str, dest_path: str) -> None:
        target_src = self._resolve_and_verify(src_path)
        target_dest = self._resolve_and_verify(dest_path)
        
        if not os.path.exists(target_src):
            raise FileNotFoundError(f"Source path '{src_path}' does not exist.")
            
        resolved_dest = target_dest
        if os.path.isdir(target_dest):
            resolved_dest = os.path.join(target_dest, os.path.basename(target_src))

        if os.path.isdir(target_src):
            shutil.copytree(target_src, target_dest)
        else:
            if os.path.isdir(target_dest):
                shutil.copy(target_src, target_dest)
            else:
                shutil.copy2(target_src, target_dest)
                
        self._trigger_auto_index(resolved_dest, "index")

    def delete(self, path: str) -> None:
        target_path = self._resolve_and_verify(path)
        if not os.path.exists(target_path):
            raise FileNotFoundError(f"Path '{path}' does not exist.")
            
        if os.path.isdir(target_path):
            shutil.rmtree(target_path)
        else:
            os.remove(target_path)
            
        self._trigger_auto_index(target_path, "delete")

    def _trigger_auto_index(self, path: str, action: str, old_path: Optional[str] = None) -> None:
        if os.getenv("ENABLE_AUTO_INDEX", "True").lower() != "true":
            return
            
        try:
            # Inline import to avoid circular dependency loop
            from tools.knowledge.service import KnowledgeService
            knowledge_service = KnowledgeService()
            
            ext = os.path.splitext(path)[1].lower()
            supported = ext in (
                ".pdf", ".docx", ".csv", ".html", ".htm", ".md", ".json", ".txt",
                ".py", ".js", ".ts", ".sh", ".bat", ".cpp", ".c", ".h", ".java", ".css"
            )
            
            if action == "delete":
                knowledge_service.delete_document(path)
            elif action == "index" and supported:
                knowledge_service.index_document(path)
            elif action == "rename":
                if old_path:
                    knowledge_service.delete_document(old_path)
                if supported:
                    knowledge_service.index_document(path)
        except Exception:
            # Fail silently to avoid interrupting filesystem operations
            pass

    def open_file(self, path: str) -> None:
        target_path = self._resolve_and_verify(path)
        if not os.path.exists(target_path):
            raise FileNotFoundError(f"Path '{path}' does not exist.")
        if not os.path.isfile(target_path):
            raise IsADirectoryError("Only files can be opened with the default application")
            
        # Execute using default OS application
        if sys.platform == "win32":
            os.startfile(target_path)
        elif sys.platform == "darwin":
            subprocess.run(["open", target_path], check=True)
        else:
            subprocess.run(["xdg-open", target_path], check=True)
