# Filesystem Tool

Provides services, router endpoints, utilities, and models for agent filesystem access.

## Files

- `filesystem_service.py`: Contains the `FilesystemService` class to list, read, and write files.
- `filesystem_models.py`: Defines request/response validation schemas (e.g. `FileItem`, `FileWriteRequest`).
- `filesystem_utils.py`: Contains auxiliary path utility functions.
- `filesystem_router.py`: API router exposing filesystem actions via FastAPI endpoints.
