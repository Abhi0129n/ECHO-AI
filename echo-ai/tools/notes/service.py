import os
import sqlite3
import json
from datetime import datetime, timezone
from typing import List, Optional
from tools.notes.schemas import NoteCreate, NoteUpdate, NoteResponse

DEFAULT_DB_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "database", "echo_ai.db")
)

class NotesService:
    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        # Ensure database directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    tags TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            conn.commit()

    def _row_to_response(self, row: sqlite3.Row) -> NoteResponse:
        try:
            tags = json.loads(row["tags"])
        except Exception:
            tags = []
        return NoteResponse(
            id=row["id"],
            title=row["title"],
            content=row["content"],
            tags=tags,
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )

    def create_note(self, note_create: NoteCreate) -> NoteResponse:
        now = datetime.now(timezone.utc).isoformat()
        tags_str = json.dumps(note_create.tags)
        
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO notes (title, content, tags, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (note_create.title, note_create.content, tags_str, now, now)
            )
            note_id = cursor.lastrowid
            conn.commit()
            
        # Retrieve and return the created note
        return self.get_note(note_id)

    def get_note(self, note_id: int) -> Optional[NoteResponse]:
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM notes WHERE id = ?", (note_id,)
            ).fetchone()
            if row:
                return self._row_to_response(row)
        return None

    def list_notes(self) -> List[NoteResponse]:
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM notes ORDER BY id DESC").fetchall()
            return [self._row_to_response(row) for row in rows]

    def update_note(self, note_id: int, note_update: NoteUpdate) -> Optional[NoteResponse]:
        existing = self.get_note(note_id)
        if not existing:
            return None

        # Build update query dynamically
        fields = []
        params = []
        
        if note_update.title is not None:
            fields.append("title = ?")
            params.append(note_update.title)
        if note_update.content is not None:
            fields.append("content = ?")
            params.append(note_update.content)
        if note_update.tags is not None:
            fields.append("tags = ?")
            params.append(json.dumps(note_update.tags))
            
        if not fields:
            return existing

        fields.append("updated_at = ?")
        params.append(datetime.now(timezone.utc).isoformat())
        params.append(note_id)

        query = f"UPDATE notes SET {', '.join(fields)} WHERE id = ?"
        
        with self._get_connection() as conn:
            conn.execute(query, tuple(params))
            conn.commit()
            
        return self.get_note(note_id)

    def delete_note(self, note_id: int) -> bool:
        with self._get_connection() as conn:
            cursor = conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
            conn.commit()
            return cursor.rowcount > 0

    def search_notes(self, query: str) -> List[NoteResponse]:
        with self._get_connection() as conn:
            # Matches search query in title, content, or tags
            like_query = f"%{query}%"
            rows = conn.execute(
                """
                SELECT * FROM notes 
                WHERE title LIKE ? OR content LIKE ? OR tags LIKE ?
                ORDER BY id DESC
                """,
                (like_query, like_query, like_query)
            ).fetchall()
            return [self._row_to_response(row) for row in rows]
