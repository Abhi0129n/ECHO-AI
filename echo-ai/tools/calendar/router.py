from fastapi import APIRouter, HTTPException, Depends, status
from typing import List
from tools.calendar.service import CalendarService
from tools.calendar.schemas import (
    CalendarEvent,
    CreateEventRequest,
    UpdateEventRequest,
    MoveEventRequest
)

router = APIRouter(prefix="/calendar", tags=["calendar"])

def get_calendar_service() -> CalendarService:
    return CalendarService(base_dir=".")

@router.get("/today", response_model=List[CalendarEvent])
def get_today_events(service: CalendarService = Depends(get_calendar_service)):
    try:
        return service.today_events()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search", response_model=List[CalendarEvent])
def search_events(q: str, service: CalendarService = Depends(get_calendar_service)):
    try:
        return service.search_events(q)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create", response_model=CalendarEvent, status_code=status.HTTP_201_CREATED)
def create_event(request: CreateEventRequest, service: CalendarService = Depends(get_calendar_service)):
    try:
        return service.create_event(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/update", response_model=CalendarEvent)
def update_event(event_id: str, request: UpdateEventRequest, service: CalendarService = Depends(get_calendar_service)):
    try:
        return service.update_event(event_id, request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/move", response_model=CalendarEvent)
def move_event(request: MoveEventRequest, service: CalendarService = Depends(get_calendar_service)):
    try:
        return service.move_event(request.event_id, request.start_time, request.end_time)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/delete", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(event_id: str, service: CalendarService = Depends(get_calendar_service)):
    try:
        service.delete_event(event_id)
        return None
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/free-slots")
def get_free_slots(
    start_time: str, 
    end_time: str, 
    duration_minutes: int = 30, 
    service: CalendarService = Depends(get_calendar_service)
):
    try:
        return service.free_slots(start_time, end_time, duration_minutes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
