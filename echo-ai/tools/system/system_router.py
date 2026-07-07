from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from tools.system.system_models import BatteryInfo, CPUInfo, MemoryInfo, DiskInfo, ProcessInfo, ApplicationRequest
from tools.system.system_service import SystemService

router = APIRouter(prefix="/system", tags=["system"])
service = SystemService()

@router.get("/cpu", response_model=CPUInfo)
def get_cpu_info():
    try:
        return service.cpu_usage()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/battery", response_model=BatteryInfo)
def get_battery_info():
    try:
        return service.battery_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/memory", response_model=MemoryInfo)
def get_memory_info():
    try:
        return service.memory_usage()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/disk", response_model=DiskInfo)
def get_disk_info(path: Optional[str] = None):
    try:
        if path:
            return service.disk_usage(path)
        return service.disk_usage()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/processes", response_model=List[ProcessInfo])
def list_processes(limit: int = 20):
    try:
        return service.list_processes(limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/open")
def open_app(request: ApplicationRequest):
    try:
        return service.open_application(request.app_name, request.args)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/close")
def close_app(app_name: str):
    try:
        return service.close_application(app_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
