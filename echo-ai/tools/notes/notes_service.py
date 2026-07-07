import os
import json
from typing import List, Optional
from tools.notes.notes_models import Note, NoteCreate, NoteUpdate
from tools.notes.notes_utils import generate_note_id, get_current_timestamp, filter_notes

class NotesService:
    def __init__(self, storage_dir: str = "uploads/notes"):
        self.storage_dir = os.path.abspath(storage_dir)
        os.makedirs(self.storage_dir, exist_ok=True)

    def _get_note_path(self, note_id: str) -> str:
        return os.path.join(self.storage_dir, f"{note_id}.json")

    def create_note(self, note_create: NoteCreate) -> Note:
        note_id = generate_note_id()
        now = get_current_timestamp()
        
        note = Note(
            id=note_id,
            title=note_create.title,
            content=note_create.content,
            tags=note_create.tags,
            created_at=now,
            updated_at=now
        )
        
        self._save_note_to_disk(note)
        return note

    def get_note(self, note_id: str) -> Optional[Note]:
        path = self._get_note_path(note_id)
        if not os.path.exists(path):
            return None
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return Note(**data)
        except Exception:
            return None

    def update_note(self, note_id: str, note_update: NoteUpdate) -> Optional[Note]:
        note = self.get_note(note_id)
        if not note:
            return None
        
        if note_update.title is not None:
            note.title = note_update.title
        if note_update.content is not None:
            note.content = note_update.content
        if note_update.tags is not None:
            note.tags = note_update.tags
            
        note.updated_at = get_current_timestamp()
        self._save_note_to_disk(note)
        return note

    def delete_note(self, note_id: str) -> bool:
        path = self._get_note_path(note_id)
        if os.path.exists(path):
            os.remove(path)
            return True
        return False

    def list_notes(self) -> List[Note]:
        notes = []
        if not os.path.exists(self.storage_dir):
            return notes
            
        for entry in os.scandir(self.storage_dir):
            if entry.is_file() and entry.name.endswith(".json"):
                try:
                    with open(entry.path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        notes.append(Note(**data))
                except Exception:
                    continue
                    
        # Sort notes by updated_at descending
        notes.sort(key=lambda x: x.updated_at, reverse=True)
        return notes

    def search_notes(self, query: str) -> List[Note]:
        notes = self.list_notes()
        return filter_notes(notes, query)

    def _save_note_to_disk(self, note: Note) -> None:
        path = self._get_note_path(note.id)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(note.dict(), f, indent=4, ensure_ascii=False)
