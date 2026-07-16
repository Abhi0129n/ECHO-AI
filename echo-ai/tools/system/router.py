from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from tools.system.service import SystemService
from tools.system.schemas import (
    CPUInfo,
    MemoryInfo,
    DiskInfo,
    BatteryInfo,
    ProcessInfo,
    OpenAppRequest,
    CloseAppRequest
)

router = APIRouter(prefix="/system", tags=["system"])

def get_system_service() -> SystemService:
    return SystemService()

@router.get("/cpu", response_model=CPUInfo)
def get_cpu(service: SystemService = Depends(get_system_service)):
    try:
        return service.cpu_usage()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/memory", response_model=MemoryInfo)
def get_memory(service: SystemService = Depends(get_system_service)):
    try:
        return service.memory_usage()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/disk", response_model=DiskInfo)
def get_disk(path: Optional[str] = None, service: SystemService = Depends(get_system_service)):
    try:
        return service.disk_usage(path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/battery", response_model=BatteryInfo)
def get_battery(service: SystemService = Depends(get_system_service)):
    try:
        return service.battery_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/processes", response_model=List[ProcessInfo])
def list_processes(limit: int = 20, service: SystemService = Depends(get_system_service)):
    try:
        return service.list_processes(limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/apps", response_model=List[str])
def list_installed_apps(service: SystemService = Depends(get_system_service)):
    try:
        return service.get_installed_applications()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/open")
def open_app(request: OpenAppRequest, service: SystemService = Depends(get_system_service)):
    try:
        return service.open_application(request.app_name, request.args)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/close")
def close_app(request: CloseAppRequest, service: SystemService = Depends(get_system_service)):
    try:
        return service.close_application(request.app_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
