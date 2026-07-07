from fastapi import APIRouter, HTTPException, status
from typing import List, Optional
from tools.notes.notes_models import Note, NoteCreate, NoteUpdate
from tools.notes.notes_service import NotesService

router = APIRouter(prefix="/notes", tags=["notes"])
service = NotesService()

@router.post("/", response_model=Note, status_code=status.HTTP_201_CREATED)
def create_note(note: NoteCreate):
    try:
        return service.create_note(note)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[Note])
def list_notes():
    try:
        return service.list_notes()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search", response_model=List[Note])
def search_notes(q: str):
    try:
        return service.search_notes(q)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{note_id}", response_model=Note)
def get_note(note_id: str):
    note = service.get_note(note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note

@router.put("/{note_id}", response_model=Note)
def update_note(note_id: str, note_update: NoteUpdate):
    note = service.update_note(note_id, note_update)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note

@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(note_id: str):
    success = service.delete_note(note_id)
    if not success:
        raise HTTPException(status_code=404, detail="Note not found")
    return None
