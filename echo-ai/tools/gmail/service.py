import os
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Dict, Any, Optional

from tools.gmail.oauth import OAuthManager
from tools.gmail.utils import extract_email, format_subject, save_attachment
from tools.gmail.schemas import EmailSummary, EmailMessage, EmailRequest, ReplyRequest, Attachment
from tools.filesystem.utils import is_safe_path

try:
    from googleapiclient.discovery import build
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False

class GmailService:
    def __init__(self, base_dir: str = "."):
        self.base_dir = os.path.abspath(base_dir)
        token_path = os.path.join(self.base_dir, "echo-ai", "config", "token.json")
        creds_path = os.path.join(self.base_dir, "echo-ai", "config", "credentials.json")
        self.oauth_manager = OAuthManager(token_path=token_path, creds_path=creds_path)

    def get_service(self):
        creds = self.oauth_manager.get_credentials()
        if GOOGLE_API_AVAILABLE and creds and creds != "MOCK_EXISTS_CREDENTIALS":
            try:
                return build('gmail', 'v1', credentials=creds)
            except Exception:
                pass
        return MockGmailService()

    def read_emails(self, label: str = "UNREAD", limit: int = 10) -> List[EmailSummary]:
        service = self.get_service()
        try:
            results = service.users().messages().list(userId='me', labelIds=[label], maxResults=limit).execute()
            messages = results.get('messages', [])[:limit]
            
            summaries = []
            for msg_meta in messages:
                msg = service.users().messages().get(
                    userId='me', id=msg_meta['id'], format='metadata', metadataHeaders=['From', 'Subject', 'Date']
                ).execute()
                
                headers = msg.get('payload', {}).get('headers', [])
                sender = "Unknown"
                subject = "(No Subject)"
                received_at = "Unknown"
                
                for header in headers:
                    if header['name'].lower() == 'from':
                        sender = header['value']
                    elif header['name'].lower() == 'subject':
                        subject = header['value']
                    elif header['name'].lower() == 'date':
                        received_at = header['value']
                        
                summaries.append(EmailSummary(
                    id=msg['id'],
                    thread_id=msg['threadId'],
                    sender=extract_email(sender),
                    subject=subject,
                    snippet=msg.get('snippet', ''),
                    received_at=received_at,
                    is_unread='UNREAD' in msg.get('labelIds', [])
                ))
            return summaries
        except Exception as e:
            raise RuntimeError(f"Error reading emails: {str(e)}")

    def search_emails(self, query: str, limit: int = 10) -> List[EmailSummary]:
        service = self.get_service()
        try:
            results = service.users().messages().list(userId='me', q=query, maxResults=limit).execute()
            messages = results.get('messages', [])[:limit]
            
            summaries = []
            for msg_meta in messages:
                msg = service.users().messages().get(
                    userId='me', id=msg_meta['id'], format='metadata', metadataHeaders=['From', 'Subject', 'Date']
                ).execute()
                
                headers = msg.get('payload', {}).get('headers', [])
                sender, subject, received_at = "Unknown", "(No Subject)", "Unknown"
                
                for header in headers:
                    if header['name'].lower() == 'from':
                        sender = header['value']
                    elif header['name'].lower() == 'subject':
                        subject = header['value']
                    elif header['name'].lower() == 'date':
                        received_at = header['value']
                        
                summaries.append(EmailSummary(
                    id=msg['id'],
                    thread_id=msg['threadId'],
                    sender=extract_email(sender),
                    subject=subject,
                    snippet=msg.get('snippet', ''),
                    received_at=received_at,
                    is_unread='UNREAD' in msg.get('labelIds', [])
                ))
            return summaries
        except Exception as e:
            raise RuntimeError(f"Error searching emails: {str(e)}")

    def get_email(self, message_id: str) -> EmailMessage:
        service = self.get_service()
        try:
            msg = service.users().messages().get(userId='me', id=message_id, format='full').execute()
            
            headers = msg.get('payload', {}).get('headers', [])
            sender, recipient, subject, received_at = "Unknown", "Unknown", "(No Subject)", "Unknown"
            
            for header in headers:
                if header['name'].lower() == 'from':
                    sender = header['value']
                elif header['name'].lower() == 'to':
                    recipient = header['value']
                elif header['name'].lower() == 'subject':
                    subject = header['value']
                elif header['name'].lower() == 'date':
                    received_at = header['value']

            # Extract body and attachments
            body_text_list = []
            body_html_list = []
            attachments = []
            
            payload = msg.get('payload', {})
            self._parse_payload_parts(payload, message_id, body_text_list, body_html_list, attachments)

            return EmailMessage(
                id=msg['id'],
                thread_id=msg['threadId'],
                sender=sender,
                recipient=recipient,
                subject=subject,
                body_text="".join(body_text_list) or msg.get('snippet', ''),
                body_html="".join(body_html_list) or None,
                received_at=received_at,
                labels=msg.get('labelIds', []),
                attachments=attachments
            )
        except Exception as e:
            raise RuntimeError(f"Error getting email: {str(e)}")

    def send_email(self, request: EmailRequest) -> Dict[str, Any]:
        service = self.get_service()
        try:
            message = MIMEMultipart()
            message['to'] = request.recipient
            message['subject'] = request.subject
            message.attach(MIMEText(request.body, 'plain'))
            
            # Attach files if any and verify paths
            for file_path in (request.attachments or []):
                if not is_safe_path(self.base_dir, file_path):
                    raise PermissionError(f"Access denied: attachment path '{file_path}' is outside the workspace")
                
                abs_file_path = os.path.abspath(os.path.join(self.base_dir, file_path))
                if os.path.exists(abs_file_path):
                    filename = os.path.basename(abs_file_path)
                    with open(abs_file_path, "rb") as f:
                        part = MIMEBase("application", "octet-stream")
                        part.set_payload(f.read())
                        encoders.encode_base64(part)
                        part.add_header("Content-Disposition", f"attachment; filename={filename}")
                        message.attach(part)
            
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            sent_msg = service.users().messages().send(userId='me', body={'raw': raw_message}).execute()
            return {"status": "success", "message_id": sent_msg['id'], "thread_id": sent_msg['threadId']}
        except Exception as e:
            raise RuntimeError(f"Error sending email: {str(e)}")

    def reply_email(self, message_id: str, request: ReplyRequest) -> Dict[str, Any]:
        service = self.get_service()
        try:
            orig = self.get_email(message_id)
            
            message = MIMEMultipart()
            message['to'] = orig.sender
            message['subject'] = format_subject(orig.subject)
            message['In-Reply-To'] = message_id
            message['References'] = message_id
            
            message.attach(MIMEText(request.body, 'plain'))
            
            # Attach files if any and verify paths
            for file_path in (request.attachments or []):
                if not is_safe_path(self.base_dir, file_path):
                    raise PermissionError(f"Access denied: attachment path '{file_path}' is outside the workspace")
                
                abs_file_path = os.path.abspath(os.path.join(self.base_dir, file_path))
                if os.path.exists(abs_file_path):
                    filename = os.path.basename(abs_file_path)
                    with open(abs_file_path, "rb") as f:
                        part = MIMEBase("application", "octet-stream")
                        part.set_payload(f.read())
                        encoders.encode_base64(part)
                        part.add_header("Content-Disposition", f"attachment; filename={filename}")
                        message.attach(part)
            
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            sent_msg = service.users().messages().send(userId='me', body={
                'raw': raw_message,
                'threadId': orig.thread_id
            }).execute()
            return {"status": "success", "message_id": sent_msg['id'], "thread_id": sent_msg['threadId']}
        except Exception as e:
            raise RuntimeError(f"Error replying to email: {str(e)}")

    def download_attachment(self, message_id: str, attachment_id: str, filename: str) -> str:
        service = self.get_service()
        try:
            att = service.users().messages().attachments().get(userId='me', messageId=message_id, id=attachment_id).execute()
            data = att.get('data', '')
            return save_attachment(data, filename, self.base_dir)
        except Exception as e:
            raise RuntimeError(f"Error downloading attachment: {str(e)}")

    def archive_email(self, message_id: str) -> None:
        service = self.get_service()
        try:
            service.users().messages().batchModify(userId='me', body={
                'ids': [message_id],
                'removeLabelIds': ['INBOX']
            }).execute()
        except Exception as e:
            raise RuntimeError(f"Error archiving email: {str(e)}")

    def delete_email(self, message_id: str) -> None:
        service = self.get_service()
        try:
            service.users().messages().trash(userId='me', id=message_id).execute()
        except Exception as e:
            raise RuntimeError(f"Error deleting email: {str(e)}")

    def _parse_payload_parts(self, part: Dict[str, Any], message_id: str, body_text_list: List[str], body_html_list: List[str], attachments: List[Attachment]):
        mime_type = part.get('mimeType', '')
        body = part.get('body', {})
        data = body.get('data', '')
        
        if mime_type == 'text/plain' and data:
            body_text_list.append(base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore'))
        elif mime_type == 'text/html' and data:
            body_html_list.append(base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore'))
            
        filename = part.get('filename', '')
        att_id = body.get('attachmentId', '')
        if filename and att_id:
            attachments.append(Attachment(
                id=att_id,
                filename=filename,
                mime_type=mime_type,
                size_bytes=body.get('size', 0)
            ))
            
        parts = part.get('parts', [])
        for p in parts:
            self._parse_payload_parts(p, message_id, body_text_list, body_html_list, attachments)

class MockGmailService:
    """Mock client mimicking googleapiclient.discovery resource methods."""
    def users(self):
        return MockUsers()

class MockUsers:
    def messages(self):
        return MockMessages()
        
    def labels(self):
        return MockLabels()

class MockMessages:
    def list(self, userId, q=None, maxResults=None, labelIds=None):
        return MockRequest(response={
            "messages": [
                {"id": "msg123", "threadId": "thread123"},
                {"id": "msg456", "threadId": "thread456"}
            ],
            "resultSizeEstimate": 2
        })
        
    def get(self, userId, id, format=None, metadataHeaders=None):
        return MockRequest(response={
            "id": id,
            "threadId": f"thread_{id}",
            "snippet": f"This is a mock snippet for message {id}.",
            "internalDate": "178239487000",
            "labelIds": ["INBOX", "UNREAD"],
            "payload": {
                "headers": [
                    {"name": "From", "value": "Sender <sender@example.com>"},
                    {"name": "To", "value": "Me <me@example.com>"},
                    {"name": "Subject", "value": f"Mock Subject {id}"},
                    {"name": "Date", "value": "Thu, 16 Jul 2026 12:00:00 +0000"}
                ],
                "body": {"size": 0},
                "parts": [
                    {
                        "mimeType": "text/plain",
                        "body": {"data": "SGVsbG8hIFRoaXMgaXMgYSBtb2NrIGVtYWlsIGJvZHku"}  # base64 for "Hello! This is a mock email body."
                    }
                ]
            }
        })
        
    def send(self, userId, body):
        return MockRequest(response={"id": "msg_sent_999", "threadId": "thread_sent_999"})
        
    def trash(self, userId, id):
        return MockRequest(response={"status": "trashed"})
        
    def batchModify(self, userId, body):
        return MockRequest(response={"status": "modified"})
        
    def attachments(self):
        return MockAttachments()

class MockAttachments:
    def get(self, userId, messageId, id):
        return MockRequest(response={"data": "dGVzdF9hdHRhY2htZW50X2NvbnRlbnQ="})  # base64 for "test_attachment_content"

class MockLabels:
    def list(self, userId):
        return MockRequest(response={
            "labels": [
                {"id": "INBOX", "name": "INBOX", "type": "system"},
                {"id": "SENT", "name": "SENT", "type": "system"}
            ]
        })

class MockRequest:
    def __init__(self, response):
        self._response = response
        
    def execute(self):
        return self._response
