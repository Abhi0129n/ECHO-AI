import os
from tools.gmail.oauth import OAuthManager

try:
    from googleapiclient.discovery import build
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False

class GmailClient:
    def __init__(self):
        self.oauth_manager = OAuthManager()

    def get_service(self):
        """
        Builds the Gmail API client.
        If authenticated and library is present, builds the live service.
        Otherwise, returns a Mock service client.
        """
        creds = self.oauth_manager.get_credentials()
        
        if GOOGLE_API_AVAILABLE and creds and creds != "MOCK_EXISTS_CREDENTIALS":
            try:
                return build('gmail', 'v1', credentials=creds)
            except Exception:
                pass
                
        return MockGmailService()

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
        
    def get(self, userId, id, format=None):
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
                    {"name": "Subject", "value": f"Mock Subject {id}"}
                ],
                "body": {"size": 0},
                "parts": [
                    {
                        "mimeType": "text/plain",
                        "body": {"data": "SGVsbG8hIFRoaXMgaXMgYSBtb2NrIGVtYWlsIGJvZHku"} # base64 for "Hello! This is a mock email body."
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
        return MockRequest(response={"data": "dGVzdF9hdHRhY2htZW50X2NvbnRlbnQ="}) # base64 for "test_attachment_content"

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
