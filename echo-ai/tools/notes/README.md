# Notes Tool

Provides CRUD operations and search functionality for notes.

## Directory Structure

- `__init__.py`: Module entry point.
- `notes_models.py`: Pydantic schemas for validation (`Note`, `NoteCreate`, `NoteUpdate`).
- `notes_service.py`: Business logic for storing and querying notes.
- `notes_router.py`: FastAPI endpoints for note operations.
- `notes_utils.py`: ID, timestamp generation and text searching/filtering helpers.
- `tests/test_notes.py`: Unit tests for notes management.

## API Endpoints

- `POST /notes/`: Create a new note.
- `GET /notes/`: List all notes (sorted by last updated).
- `GET /notes/search?q={query}`: Search notes by title, content, or tags.
- `GET /notes/{note_id}`: Get a note by ID.
- `PUT /notes/{note_id}`: Update a note by ID.
- `DELETE /notes/{note_id}`: Delete a note by ID.
