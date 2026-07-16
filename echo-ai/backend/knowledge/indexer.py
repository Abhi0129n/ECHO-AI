import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from backend.embeddings.embedder import LocalEmbedder
from backend.vectorstore.faiss_store import FAISSStoreManager
from backend.knowledge.loader import DocumentLoader
from backend.knowledge.metadata import MetadataRegistry

logger = logging.getLogger("echo_ai.indexer")

class DocumentIndexer:
    def __init__(
        self,
        index_path: Optional[str] = None,
        metadata_path: Optional[str] = None,
        embedder: Optional[LocalEmbedder] = None
    ):
        self.embedder = embedder or LocalEmbedder()
        self.index_path = index_path or os.getenv("FAISS_INDEX_PATH", "echo-ai/database/faiss_index")
        self.metadata_path = metadata_path or os.getenv("METADATA_PATH", "echo-ai/database/kb_metadata.json")

        self.registry = MetadataRegistry(metadata_path=self.metadata_path)
        self.faiss_manager = FAISSStoreManager(index_path=self.index_path, embeddings=self.embedder)
        self.loader = DocumentLoader()

    def index_document(self, file_path: str, force: bool = False) -> Dict[str, Any]:
        """
        Loads, splits, embeds, and indexes a file into FAISS.
        Checks modified timestamp to avoid indexing duplicates unless force=True.
        """
        file_path = os.path.abspath(file_path)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        mtime = datetime.fromtimestamp(os.path.getmtime(file_path), timezone.utc).isoformat()

        # Check existing registration to avoid redundant work
        record = self.registry.get_document(file_path)
        if record and record.get("last_modified") == mtime and not force:
            logger.info(f"Document already indexed and unchanged: {file_path}")
            return {
                "success": True,
                "status": "skipped",
                "document_id": record["document_id"],
                "chunks_count": len(record["chunk_ids"])
            }

        # Clear previously indexed vector chunks if updating
        if record:
            self.delete_document(file_path)

        logger.info(f"Indexing document: {file_path}")
        chunks = self.loader.load_and_split(file_path)

        if not chunks:
            return {
                "success": True,
                "status": "empty",
                "document_id": None,
                "chunks_count": 0
            }

        # Index vectors and retrieve auto-generated chunk keys
        chunk_ids = self.faiss_manager.add_documents(chunks)

        # Register metadata records
        doc_id = chunks[0].metadata["document_id"]
        filename = chunks[0].metadata["filename"]
        file_type = chunks[0].metadata["file_type"]

        self.registry.register_document(
            file_path=file_path,
            document_id=doc_id,
            filename=filename,
            file_type=file_type,
            last_modified=mtime,
            chunk_ids=chunk_ids
        )

        return {
            "success": True,
            "status": "indexed",
            "document_id": doc_id,
            "chunks_count": len(chunk_ids)
        }

    def delete_document(self, file_path: str) -> bool:
        """Deletes document chunk vectors from FAISS and drops metadata registration."""
        file_path = os.path.abspath(file_path)
        record = self.registry.get_document(file_path)
        if not record:
            return False

        # Clear vector segments
        chunk_ids = record.get("chunk_ids", [])
        if chunk_ids:
            self.faiss_manager.delete_documents(chunk_ids)

        # Drop record entry
        self.registry.remove_document(file_path)
        return True

    def reindex_document(self, file_path: str) -> Dict[str, Any]:
        """Forces document index reload."""
        return self.index_document(file_path, force=True)

    def reindex_all(self) -> Dict[str, int]:
        """Wipes and index reloads all registered documents."""
        records = self.registry.list_documents()
        logger.info(f"Re-indexing all {len(records)} registered documents.")

        all_chunks = []
        doc_registrations = []

        for rec in records:
            path = rec["file_path"]
            if os.path.exists(path):
                mtime = datetime.fromtimestamp(os.path.getmtime(path), timezone.utc).isoformat()
                chunks = self.loader.load_and_split(path)
                if chunks:
                    all_chunks.extend(chunks)
                    doc_registrations.append((path, chunks, mtime))
            else:
                self.registry.remove_document(path)

        if not all_chunks:
            # Rebuild clean
            self.faiss_manager.rebuild_index([], [])
            return {"indexed_files": 0, "total_chunks": 0}

        # Build clean index operation
        if self.faiss_manager.vectorstore is not None:
            self.faiss_manager.rebuild_index(all_chunks)
            chunk_ids = list(self.faiss_manager.vectorstore.docstore._dict.keys())
        else:
            chunk_ids = self.faiss_manager.add_documents(all_chunks)

        # Map back chunk IDs using offset slice logic
        chunk_offset = 0
        for path, chunks, mtime in doc_registrations:
            num_chunks = len(chunks)
            doc_chunk_ids = chunk_ids[chunk_offset : chunk_offset + num_chunks]
            chunk_offset += num_chunks

            doc_id = chunks[0].metadata["document_id"]
            filename = chunks[0].metadata["filename"]
            file_type = chunks[0].metadata["file_type"]

            self.registry.register_document(
                file_path=path,
                document_id=doc_id,
                filename=filename,
                file_type=file_type,
                last_modified=mtime,
                chunk_ids=doc_chunk_ids
            )

        return {
            "indexed_files": len(doc_registrations),
            "total_chunks": len(chunk_ids)
        }
