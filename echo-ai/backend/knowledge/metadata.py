import os
import json
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("echo_ai.metadata_registry")

class MetadataRegistry:
    def __init__(self, metadata_path: Optional[str] = None):
        if metadata_path is None:
            metadata_path = os.getenv("METADATA_PATH", "echo-ai/database/kb_metadata.json")
        self.metadata_path = os.path.abspath(metadata_path)
        self.registry: Dict[str, Dict[str, Any]] = {}
        self.load()

    def load(self) -> None:
        """Loads metadata registry from local disk."""
        if os.path.exists(self.metadata_path):
            try:
                with open(self.metadata_path, "r", encoding="utf-8") as f:
                    self.registry = json.load(f)
                logger.info(f"Loaded metadata registry from {self.metadata_path}")
            except Exception as e:
                logger.error(f"Failed to load metadata registry: {str(e)}")
                self.registry = {}
        else:
            self.registry = {}

    def save(self) -> None:
        """Saves current metadata registry state to disk."""
        try:
            os.makedirs(os.path.dirname(self.metadata_path), exist_ok=True)
            with open(self.metadata_path, "w", encoding="utf-8") as f:
                json.dump(self.registry, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save metadata registry: {str(e)}")

    def register_document(
        self, 
        file_path: str, 
        document_id: str, 
        filename: str, 
        file_type: str, 
        last_modified: str, 
        chunk_ids: List[str]
    ) -> None:
        """Adds or updates a document registration entry."""
        abs_path = os.path.abspath(file_path)
        self.registry[abs_path] = {
            "document_id": document_id,
            "filename": filename,
            "file_type": file_type,
            "last_modified": last_modified,
            "chunk_ids": chunk_ids
        }
        self.save()

    def get_document(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Retrieves registration record matching file path."""
        abs_path = os.path.abspath(file_path)
        return self.registry.get(abs_path)

    def remove_document(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Removes and returns registration record matching file path."""
        abs_path = os.path.abspath(file_path)
        if abs_path in self.registry:
            doc_data = self.registry.pop(abs_path)
            self.save()
            return doc_data
        return None

    def list_documents(self) -> List[Dict[str, Any]]:
        """Lists all registered documents."""
        return [
            {"file_path": path, **data} for path, data in self.registry.items()
        ]
