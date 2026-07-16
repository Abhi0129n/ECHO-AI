from fastapi import APIRouter, HTTPException, Depends, status
from backend.chat.schemas import ChatRequest, ChatResponse
from backend.chat.service import ChatService

from tools.notes.router import get_notes_service
from tools.notes.service import NotesService

router = APIRouter(tags=["chat"])

def get_chat_service(notes_service: NotesService = Depends(get_notes_service)) -> ChatService:
    return ChatService(base_dir=".", notes_service=notes_service)

@router.post("/chat", response_model=ChatResponse)
def chat_message(request: ChatRequest, service: ChatService = Depends(get_chat_service)):
    response = service.handle_chat_message(request.message, request.session_id)
    
    if not response.success:
        if response.requires_clarification:
            return response
            
        err = response.error or ""
        err_lower = err.lower()
        
        # Map specific internal errors to proper HTTP status codes
        if "unauthorized" in err_lower or "api_key" in err_lower or "credentials" in err_lower or "auth" in err_lower or "authentication" in err_lower:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=err)
            
        elif "invalid json" in err_lower or "missing required" in err_lower or "validation failed" in err_lower or "unknown tool" in err_lower or "unknown action" in err_lower or "missing parameter" in err_lower:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err)
            
        elif "access denied" in err_lower or "permission error" in err_lower:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=err)
            
        elif "not found" in err_lower or "no such" in err_lower:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=err)
            
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=err)
            
    return response
