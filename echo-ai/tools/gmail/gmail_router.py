from fastapi import APIRouter, HTTPException, Query, status
from typing import List, Optional, Dict, Any
from tools.gmail.gmail_models import EmailSummary, EmailMessage, EmailRequest, ReplyRequest
from tools.gmail.gmail_service import GmailService

router = APIRouter(prefix="/gmail", tags=["gmail"])
service = GmailService()

@router.get("/unread", response_model=List[EmailSummary])
def get_unread_emails(limit: int = 10):
    try:
        return service.read_emails(label="UNREAD", limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search", response_model=List[EmailSummary])
def search_emails(q: str, limit: int = 10):
    try:
        return service.search_emails(query=q, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/message/{message_id}", response_model=EmailMessage)
def get_email_details(message_id: str):
    try:
        return service.get_email(message_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/send")
def send_email(request: EmailRequest):
    try:
        return service.send_email(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reply")
def reply_email(message_id: str, request: ReplyRequest):
    try:
        return service.reply_email(message_id, request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/attachments")
def download_attachment(message_id: str, attachment_id: str, filename: str):
    try:
        file_path = service.download_attachment(message_id, attachment_id, filename)
        return {"status": "success", "file_path": file_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/message/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_email(message_id: str):
    try:
        service.delete_email(message_id)
        return None
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
