from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional, Union
from tools.notes.service import NotesService
from tools.notes.schemas import NoteCreate, NoteUpdate, NoteResponse

router = APIRouter(prefix="/notes", tags=["notes"])

def get_notes_service() -> NotesService:
    return NotesService()

@router.post("/create", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
def create_note(note: NoteCreate, service: NotesService = Depends(get_notes_service)):
    try:
        return service.create_note(note)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/read", response_model=Union[NoteResponse, List[NoteResponse]])
def read_note(id: Optional[int] = None, service: NotesService = Depends(get_notes_service)):
    try:
        if id is not None:
            note = service.get_note(id)
            if not note:
                raise HTTPException(status_code=404, detail=f"Note with ID {id} not found")
            return note
        else:
            return service.list_notes()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/update", response_model=NoteResponse)
def update_note(id: int, note_update: NoteUpdate, service: NotesService = Depends(get_notes_service)):
    try:
        note = service.update_note(id, note_update)
        if not note:
            raise HTTPException(status_code=404, detail=f"Note with ID {id} not found")
        return note
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/delete")
def delete_note(id: int, service: NotesService = Depends(get_notes_service)):
    try:
        success = service.delete_note(id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Note with ID {id} not found")
        return {"status": "success", "message": f"Note with ID {id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search", response_model=List[NoteResponse])
def search_notes(q: str, service: NotesService = Depends(get_notes_service)):
    try:
        return service.search_notes(q)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
