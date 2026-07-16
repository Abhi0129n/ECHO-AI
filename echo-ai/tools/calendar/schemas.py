from pydantic import BaseModel, Field
from typing import Optional, List, Dict

class ReminderRequest(BaseModel):
    method: str = Field(..., description="Method of reminder (e.g. 'email', 'popup')")
    minutes_before: int = Field(..., description="Number of minutes before event for reminder")

class CalendarEvent(BaseModel):
    id: str
    summary: str
    description: Optional[str] = None
    location: Optional[str] = None
    start_time: str
    end_time: str
    attendees: List[str] = []
    reminders: List[ReminderRequest] = []

class CreateEventRequest(BaseModel):
    summary: str = Field(..., description="Event title/summary")
    description: Optional[str] = Field(None, description="Event description")
    location: Optional[str] = Field(None, description="Event location")
    start_time: str = Field(..., description="ISO-8601 start date-time string (e.g. '2026-07-16T10:00:00Z')")
    end_time: str = Field(..., description="ISO-8601 end date-time string (e.g. '2026-07-16T11:00:00Z')")
    attendees: Optional[List[str]] = Field(default_factory=list, description="List of attendee email addresses")
    reminders: Optional[List[ReminderRequest]] = Field(default_factory=list, description="List of reminder overrides")

class UpdateEventRequest(BaseModel):
    summary: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    attendees: Optional[List[str]] = None
    reminders: Optional[List[ReminderRequest]] = None

class MoveEventRequest(BaseModel):
    event_id: str = Field(..., description="ID of the event to move")
    start_time: str = Field(..., description="New ISO-8601 start date-time string")
    end_time: str = Field(..., description="New ISO-8601 end date-time string")
