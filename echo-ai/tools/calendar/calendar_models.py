from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class ReminderRequest(BaseModel):
    method: str  # 'email', 'popup'
    minutes_before: int

class CalendarEvent(BaseModel):
    id: str
    summary: str
    description: Optional[str] = None
    location: Optional[str] = None
    start_time: str  # ISO-8601 string
    end_time: str    # ISO-8601 string
    attendees: List[str] = []
    reminders: List[ReminderRequest] = []

class CreateEventRequest(BaseModel):
    summary: str
    description: Optional[str] = None
    location: Optional[str] = None
    start_time: str
    end_time: str
    attendees: Optional[List[str]] = []
    reminders: Optional[List[ReminderRequest]] = []

class UpdateEventRequest(BaseModel):
    summary: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    attendees: Optional[List[str]] = None
    reminders: Optional[List[ReminderRequest]] = None
