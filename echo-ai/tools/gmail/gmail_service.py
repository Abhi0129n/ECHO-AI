import base64
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Dict, Any, Optional
from tools.gmail.gmail_client import GmailClient
from tools.gmail.gmail_models import EmailSummary, EmailMessage, EmailRequest, ReplyRequest, Attachment
from tools.gmail.gmail_utils import extract_email, format_subject, save_attachment

class GmailService:
    def __init__(self):
        self.client = GmailClient()
        self.service = self.client.get_service()

    def read_emails(self, label: str = "UNREAD", limit: int = 10) -> List[EmailSummary]:
        try:
            results = self.service.users().messages().list(userId='me', labelIds=[label], maxResults=limit).execute()
            messages = results.get('messages', [])
            
            summaries = []
            for msg_meta in messages:
                msg = self.service.users().messages().get(userId='me', id=msg_meta['id'], format='metadata', metadataHeaders=['From', 'Subject', 'Date']).execute()
                
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
        try:
            results = self.service.users().messages().list(userId='me', q=query, maxResults=limit).execute()
            messages = results.get('messages', [])
            
            summaries = []
            for msg_meta in messages:
                msg = self.service.users().messages().get(userId='me', id=msg_meta['id'], format='metadata', metadataHeaders=['From', 'Subject', 'Date']).execute()
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
        try:
            msg = self.service.users().messages().get(userId='me', id=message_id, format='full').execute()
            
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

            # Extract body
            body_text = ""
            body_html = ""
            attachments = []
            
            payload = msg.get('payload', {})
            self._parse_payload_parts(payload, message_id, body_text, body_html, attachments)

            return EmailMessage(
                id=msg['id'],
                thread_id=msg['threadId'],
                sender=sender,
                recipient=recipient,
                subject=subject,
                body_text=body_text or msg.get('snippet', ''),
                body_html=body_html or None,
                received_at=received_at,
                labels=msg.get('labelIds', []),
                attachments=attachments
            )
        except Exception as e:
            raise RuntimeError(f"Error getting email: {str(e)}")

    def send_email(self, request: EmailRequest) -> Dict[str, Any]:
        try:
            message = MIMEMultipart()
            message['to'] = request.recipient
            message['subject'] = request.subject
            message.attach(MIMEText(request.body, 'plain'))
            
            # Attach files if any
            for file_path in (request.attachments or []):
                if os.path.exists(file_path):
                    filename = os.path.basename(file_path)
                    with open(file_path, "rb") as f:
                        part = MIMEBase("application", "octet-stream")
                        part.set_payload(f.read())
                        encoders.encode_base64(part)
                        part.add_header("Content-Disposition", f"attachment; filename={filename}")
                        message.attach(part)
            
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            sent_msg = self.service.users().messages().send(userId='me', body={'raw': raw_message}).execute()
            return {"status": "success", "message_id": sent_msg['id'], "thread_id": sent_msg['threadId']}
        except Exception as e:
            raise RuntimeError(f"Error sending email: {str(e)}")

    def reply_email(self, message_id: str, request: ReplyRequest) -> Dict[str, Any]:
        try:
            orig = self.get_email(message_id)
            
            message = MIMEMultipart()
            message['to'] = orig.sender
            message['subject'] = format_subject(orig.subject)
            message['In-Reply-To'] = message_id
            message['References'] = message_id
            
            message.attach(MIMEText(request.body, 'plain'))
            
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            sent_msg = self.service.users().messages().send(userId='me', body={
                'raw': raw_message,
                'threadId': orig.thread_id
            }).execute()
            return {"status": "success", "message_id": sent_msg['id'], "thread_id": sent_msg['threadId']}
        except Exception as e:
            raise RuntimeError(f"Error replying to email: {str(e)}")

    def download_attachment(self, message_id: str, attachment_id: str, filename: str) -> str:
        try:
            att = self.service.users().messages().attachments().get(userId='me', messageId=message_id, id=attachment_id).execute()
            data = att.get('data', '')
            return save_attachment(data, filename)
        except Exception as e:
            raise RuntimeError(f"Error downloading attachment: {str(e)}")

    def archive_email(self, message_id: str) -> None:
        try:
            self.service.users().messages().batchModify(userId='me', body={
                'ids': [message_id],
                'removeLabelIds': ['INBOX']
            }).execute()
        except Exception as e:
            raise RuntimeError(f"Error archiving email: {str(e)}")

    def delete_email(self, message_id: str) -> None:
        try:
            self.service.users().messages().trash(userId='me', id=message_id).execute()
        except Exception as e:
            raise RuntimeError(f"Error deleting email: {str(e)}")

    def _parse_payload_parts(self, part: Dict[str, Any], message_id: str, body_text: str, body_html: str, attachments: List[Attachment]):
        mime_type = part.get('mimeType', '')
        body = part.get('body', {})
        data = body.get('data', '')
        
        if mime_type == 'text/plain' and data:
            body_text += base64.urlsafe_b64decode(data).decode('utf-8')
        elif mime_type == 'text/html' and data:
            body_html += base64.urlsafe_b64decode(data).decode('utf-8')
            
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
            self._parse_payload_parts(p, message_id, body_text, body_html, attachments)
