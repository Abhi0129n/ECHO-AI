from datetime import datetime, timedelta, date
from typing import List, Dict, Any, Optional
from tools.calendar.oauth import CalendarOAuthManager
from tools.calendar.calendar_models import CalendarEvent, CreateEventRequest, UpdateEventRequest, ReminderRequest
from tools.calendar.calendar_utils import validate_iso_format, find_free_slots

try:
    from googleapiclient.discovery import build
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False

class CalendarService:
    def __init__(self):
        self.oauth_manager = CalendarOAuthManager()
        self.service = self._get_service()

    def _get_service(self):
        creds = self.oauth_manager.get_credentials()
        if GOOGLE_API_AVAILABLE and creds and creds != "MOCK_EXISTS_CREDENTIALS":
            try:
                return build('calendar', 'v3', credentials=creds)
            except Exception:
                pass
        return MockCalendarResource()

    def today_events(self) -> List[CalendarEvent]:
        now_dt = datetime.utcnow()
        start = datetime(now_dt.year, now_dt.month, now_dt.day, 0, 0, 0).isoformat() + "Z"
        end = datetime(now_dt.year, now_dt.month, now_dt.day, 23, 59, 59).isoformat() + "Z"
        return self._list_events(start, end)

    def search_events(self, query: str) -> List[CalendarEvent]:
        # Fetch upcoming events and match description/summary
        now = datetime.utcnow().isoformat() + "Z"
        events = self._list_events(now, limit=100)
        
        matched = []
        for ev in events:
            summary_match = query.lower() in ev.summary.lower()
            desc_match = ev.description and query.lower() in ev.description.lower()
            if summary_match or desc_match:
                matched.append(ev)
        return matched

    def create_event(self, request: CreateEventRequest) -> CalendarEvent:
        if not validate_iso_format(request.start_time) or not validate_iso_format(request.end_time):
            raise ValueError("Start time and End time must be valid ISO-8601 strings")
            
        body = {
            'summary': request.summary,
            'description': request.description,
            'location': request.location,
            'start': {'dateTime': request.start_time},
            'end': {'dateTime': request.end_time},
            'attendees': [{'email': email} for email in (request.attendees or [])],
            'reminders': {
                'useDefault': False,
                'overrides': [{'method': r.method, 'minutes': r.minutes_before} for r in (request.reminders or [])]
            }
        }
        
        try:
            created = self.service.events().insert(calendarId='primary', body=body).execute()
            return self._parse_api_event(created)
        except Exception as e:
            raise RuntimeError(f"Error creating event: {str(e)}")

    def update_event(self, event_id: str, request: UpdateEventRequest) -> CalendarEvent:
        try:
            # First fetch
            existing = self.service.events().get(calendarId='primary', eventId=event_id).execute()
            
            if request.summary is not None:
                existing['summary'] = request.summary
            if request.description is not None:
                existing['description'] = request.description
            if request.location is not None:
                existing['location'] = request.location
            if request.start_time is not None:
                if not validate_iso_format(request.start_time):
                    raise ValueError("Invalid ISO-8601 start_time")
                existing['start'] = {'dateTime': request.start_time}
            if request.end_time is not None:
                if not validate_iso_format(request.end_time):
                    raise ValueError("Invalid ISO-8601 end_time")
                existing['end'] = {'dateTime': request.end_time}
            if request.attendees is not None:
                existing['attendees'] = [{'email': email} for email in request.attendees]
            if request.reminders is not None:
                existing['reminders'] = {
                    'useDefault': False,
                    'overrides': [{'method': r.method, 'minutes': r.minutes_before} for r in request.reminders]
                }
                
            updated = self.service.events().update(calendarId='primary', eventId=event_id, body=existing).execute()
            return self._parse_api_event(updated)
        except Exception as e:
            raise RuntimeError(f"Error updating event: {str(e)}")

    def delete_event(self, event_id: str) -> None:
        try:
            self.service.events().delete(calendarId='primary', eventId=event_id).execute()
        except Exception as e:
            raise RuntimeError(f"Error deleting event: {str(e)}")

    def free_slots(self, start_time: str, end_time: str, duration_minutes: int = 30) -> List[Dict[str, str]]:
        if not validate_iso_format(start_time) or not validate_iso_format(end_time):
            raise ValueError("Start time and End time must be ISO-8601 formats")
            
        events = self._list_events(start_time, end_time)
        
        # Parse into datetimes
        def parse_dt(s: str) -> datetime:
            s = s.rstrip('Z')
            if '.' in s:
                s = s.split('.')[0]
            return datetime.fromisoformat(s)
            
        start_dt = parse_dt(start_time)
        end_dt = parse_dt(end_time)
        
        busy = []
        for ev in events:
            busy.append((parse_dt(ev.start_time), parse_dt(ev.end_time)))
            
        slots = find_free_slots(busy, start_dt, end_dt, timedelta(minutes=duration_minutes))
        
        return [{
            "start": s[0].isoformat() + "Z",
            "end": s[1].isoformat() + "Z"
        } for s in slots]

    def _list_events(self, time_min: str, time_max: Optional[str] = None, limit: int = 25) -> List[CalendarEvent]:
        try:
            query = self.service.events().list(
                calendarId='primary',
                timeMin=time_min,
                timeMax=time_max,
                maxResults=limit,
                singleEvents=True,
                orderBy='startTime'
            )
            res = query.execute()
            items = res.get('items', [])
            return [self._parse_api_event(item) for item in items]
        except Exception as e:
            raise RuntimeError(f"Error listing calendar events: {str(e)}")

    def _parse_api_event(self, item: Dict[str, Any]) -> CalendarEvent:
        start = item.get('start', {})
        start_time = start.get('dateTime') or start.get('date') or ""
        end = item.get('end', {})
        end_time = end.get('dateTime') or end.get('date') or ""
        
        attendees = [a.get('email') for a in item.get('attendees', []) if a.get('email')]
        
        reminders_list = []
        for override in item.get('reminders', {}).get('overrides', []):
            reminders_list.append(ReminderRequest(
                method=override.get('method', 'popup'),
                minutes_before=override.get('minutes', 15)
            ))
            
        return CalendarEvent(
            id=item.get('id', ''),
            summary=item.get('summary', '(No Summary)'),
            description=item.get('description'),
            location=item.get('location'),
            start_time=start_time,
            end_time=end_time,
            attendees=attendees,
            reminders=reminders_list
        )

# Mock resource structure for Google Calendar API
class MockCalendarResource:
    def events(self):
        return MockEvents()

class MockEvents:
    def list(self, calendarId, timeMin, timeMax=None, maxResults=25, singleEvents=True, orderBy=None):
        now_date = datetime.utcnow().strftime("%Y-%m-%d")
        return MockRequest(response={
            "items": [
                {
                    "id": "event1",
                    "summary": "Weekly Status Meeting",
                    "description": "Catch-up with the project development team.",
                    "location": "Google Meet",
                    "start": {"dateTime": f"{now_date}T10:00:00Z"},
                    "end": {"dateTime": f"{now_date}T11:00:00Z"},
                    "attendees": [{"email": "colleague@example.com"}],
                    "reminders": {"overrides": [{"method": "popup", "minutes": 10}]}
                },
                {
                    "id": "event2",
                    "summary": "Lunch with Manager",
                    "description": "Discuss career growth progress.",
                    "location": "Cafe Gusto",
                    "start": {"dateTime": f"{now_date}T13:00:00Z"},
                    "end": {"dateTime": f"{now_date}T14:00:00Z"},
                    "attendees": [],
                    "reminders": {"overrides": []}
                }
            ]
        })

    def get(self, calendarId, eventId):
        now_date = datetime.utcnow().strftime("%Y-%m-%d")
        return MockRequest(response={
            "id": eventId,
            "summary": "Sample Event",
            "description": "Sample Description",
            "location": "Online",
            "start": {"dateTime": f"{now_date}T15:00:00Z"},
            "end": {"dateTime": f"{now_date}T16:00:00Z"}
        })

    def insert(self, calendarId, body):
        body['id'] = "new_event_123"
        return MockRequest(response=body)

    def update(self, calendarId, eventId, body):
        body['id'] = eventId
        return MockRequest(response=body)

    def delete(self, calendarId, eventId):
        return MockRequest(response={"status": "deleted"})

class MockRequest:
    def __init__(self, response):
        self._response = response
    def execute(self):
        return self._response
