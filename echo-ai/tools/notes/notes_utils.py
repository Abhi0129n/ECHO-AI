import uuid
from datetime import datetime
from typing import List
from tools.notes.notes_models import Note

def generate_note_id() -> str:
    return str(uuid.uuid4())

def get_current_timestamp() -> str:
    return datetime.utcnow().isoformat() + "Z"

def filter_notes(notes: List[Note], query: str) -> List[Note]:
    if not query:
        return notes
    
    query = query.lower()
    results = []
    for note in notes:
        title_match = query in note.title.lower()
        content_match = query in note.content.lower()
        tag_match = any(query in tag.lower() for tag in note.tags)
        
        if title_match or content_match or tag_match:
            results.append(note)
            
    return results
