import os
import sqlite3
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from langchain_core.documents import Document
from backend.embeddings.embedder import LocalEmbedder
from backend.vectorstore.faiss_store import FAISSStoreManager

logger = logging.getLogger("echo_ai.long_term_memory")

DEFAULT_DB_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "database", "echo_ai.db")
)
DEFAULT_MEMORY_INDEX_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "database", "memory_faiss_index")
)

class LongTermMemory:
    def __init__(self, db_path: str = DEFAULT_DB_PATH, index_path: str = DEFAULT_MEMORY_INDEX_PATH):
        self.db_path = db_path
        self.index_path = index_path
        
        # Initialize SQLite database directory and tables
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()
        
        # Initialize Embeddings and FAISS store for memories
        self.embedder = LocalEmbedder()
        self.faiss_manager = FAISSStoreManager(index_path=self.index_path, embeddings=self.embedder)

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS long_term_memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            conn.commit()

    def add_memory(self, category: str, key: str, value: str) -> Dict[str, Any]:
        """Adds a memory to SQLite and index it semantically in FAISS."""
        now = datetime.now(timezone.utc).isoformat()
        
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO long_term_memories (category, key, value, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (category, key, value, now, now)
            )
            memory_id = cursor.lastrowid
            conn.commit()

        # Build memory content for semantic representation
        memory_content = f"Category: {category} | Key: {key} | Details: {value}"
        doc = Document(
            page_content=memory_content,
            metadata={"memory_id": memory_id, "category": category, "key": key}
        )
        
        # Add to FAISS using SQLite row ID as vector key to match deletes/updates
        self.faiss_manager.add_documents([doc], ids=[str(memory_id)])
        logger.info(f"Registered long term memory ID {memory_id} under category '{category}'")

        return {
            "id": memory_id,
            "category": category,
            "key": key,
            "value": value,
            "created_at": now,
            "updated_at": now
        }

    def delete_memory(self, memory_id: int) -> bool:
        """Deletes memory from SQLite and FAISS."""
        with self._get_connection() as conn:
            cursor = conn.execute("DELETE FROM long_term_memories WHERE id = ?", (memory_id,))
            rows_affected = cursor.rowcount
            conn.commit()

        if rows_affected > 0:
            # Delete corresponding vector segment
            self.faiss_manager.delete_documents([str(memory_id)])
            logger.info(f"Deleted long term memory ID {memory_id}")
            return True
        return False

    def list_memories(self) -> List[Dict[str, Any]]:
        """Lists all registered memory rows."""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM long_term_memories").fetchall()
            return [dict(r) for r in rows]

    def search_memories(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """
        Searches memories semantically using similarity search over memory vectors.
        Retrieves complete database rows based on matching IDs.
        """
        # Search memory FAISS store
        results = self.faiss_manager.similarity_search_with_score(query, k=limit, threshold=0.1)
        if not results:
            return []

        memory_ids = []
        for item in results:
            doc = item["document"]
            mem_id = doc.metadata.get("memory_id")
            if mem_id is not None:
                memory_ids.append(int(mem_id))

        if not memory_ids:
            return []

        # Query database for the matched memory IDs
        placeholders = ",".join("?" for _ in memory_ids)
        with self._get_connection() as conn:
            rows = conn.execute(
                f"SELECT * FROM long_term_memories WHERE id IN ({placeholders})",
                memory_ids
            ).fetchall()
            
            # Map database rows to score weights
            row_dict = {row["id"]: dict(row) for row in rows}
            
            ranked_memories = []
            for item in results:
                doc = item["document"]
                mem_id = int(doc.metadata.get("memory_id"))
                if mem_id in row_dict:
                    record = row_dict[mem_id].copy()
                    record["score"] = item["score"]
                    ranked_memories.append(record)
                    
            return ranked_memories

    def clear_memories(self) -> None:
        """Wipes SQLite and FAISS memory databases."""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM long_term_memories")
            conn.commit()
            
        self.faiss_manager.rebuild_index([], [])
        logger.info("Cleared all long term memory records.")
