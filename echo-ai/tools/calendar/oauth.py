import os
from typing import Any, Optional

class CalendarOAuthManager:
    def __init__(self, token_path: str = "config/token_calendar.json", creds_path: str = "config/credentials.json"):
        self.token_path = token_path
        self.creds_path = creds_path

    def get_credentials(self) -> Optional[Any]:
        try:
            from google.oauth2.credentials import Credentials
            from google.auth.transport.requests import Request
            
            creds = None
            if os.path.exists(self.token_path):
                creds = Credentials.from_authorized_user_file(self.token_path)
                
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                with open(self.token_path, "w") as token_file:
                    token_file.write(creds.to_json())
                    
            return creds
        except ImportError:
            pass
            
        if os.path.exists(self.token_path):
            return "MOCK_EXISTS_CREDENTIALS"
        return None

    def is_authenticated(self) -> bool:
        return self.get_credentials() is not None
