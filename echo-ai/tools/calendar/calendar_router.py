from fastapi import APIRouter, HTTPException, Query, status
from typing import List, Optional
from tools.calendar.calendar_models import CalendarEvent, CreateEventRequest, UpdateEventRequest
from tools.calendar.calendar_service import CalendarService

router = APIRouter(prefix="/calendar", tags=["calendar"])
service = CalendarService()

@router.get("/today", response_model=List[CalendarEvent])
def get_today_events():
    try:
        return service.today_events()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search", response_model=List[CalendarEvent])
def search_events(q: str):
    try:
        return service.search_events(q)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create", response_model=CalendarEvent, status_code=status.HTTP_201_CREATED)
def create_event(request: CreateEventRequest):
    try:
        return service.create_event(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/update", response_model=CalendarEvent)
def update_event(event_id: str, request: UpdateEventRequest):
    try:
        return service.update_event(event_id, request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/delete", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(event_id: str):
    try:
        service.delete_event(event_id)
        return None
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/free-slots")
def get_free_slots(start_time: str, end_time: str, duration_minutes: int = 30):
    try:
        return service.free_slots(start_time, end_time, duration_minutes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
