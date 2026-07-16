from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import List, Dict, Any, Optional
from tools.gmail.service import GmailService
from tools.gmail.schemas import (
    EmailSummary,
    EmailMessage,
    EmailRequest,
    ReplyRequest
)

router = APIRouter(prefix="/gmail", tags=["gmail"])

def get_gmail_service() -> GmailService:
    return GmailService(base_dir=".")

@router.get("/unread", response_model=List[EmailSummary])
def get_unread_emails(limit: int = 10, service: GmailService = Depends(get_gmail_service)):
    try:
        return service.read_emails(label="UNREAD", limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search", response_model=List[EmailSummary])
def search_emails(q: str, limit: int = 10, service: GmailService = Depends(get_gmail_service)):
    try:
        return service.search_emails(query=q, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/message/{message_id}", response_model=EmailMessage)
def get_email_details(message_id: str, service: GmailService = Depends(get_gmail_service)):
    try:
        return service.get_email(message_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/send")
def send_email(request: EmailRequest, service: GmailService = Depends(get_gmail_service)):
    try:
        return service.send_email(request)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reply")
def reply_email(message_id: str, request: ReplyRequest, service: GmailService = Depends(get_gmail_service)):
    try:
        return service.reply_email(message_id, request)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/archive")
def archive_email(message_id: str, service: GmailService = Depends(get_gmail_service)):
    try:
        service.archive_email(message_id)
        return {"status": "success", "message": f"Message '{message_id}' archived successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/attachments")
def download_attachment(
    message_id: str, 
    attachment_id: str, 
    filename: str, 
    service: GmailService = Depends(get_gmail_service)
):
    try:
        file_path = service.download_attachment(message_id, attachment_id, filename)
        return {"status": "success", "file_path": file_path}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/message/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_email(message_id: str, service: GmailService = Depends(get_gmail_service)):
    try:
        service.delete_email(message_id)
        return None
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
