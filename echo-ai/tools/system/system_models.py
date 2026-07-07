from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class BatteryInfo(BaseModel):
    percent: float
    power_plugged: Optional[bool] = None
    secs_left: Optional[int] = None

class CPUInfo(BaseModel):
    percent_usage: float
    cores_physical: int
    cores_logical: int
    frequency_mhz: Optional[float] = None

class MemoryInfo(BaseModel):
    total_gb: float
    available_gb: float
    used_gb: float
    percent_used: float

class DiskInfo(BaseModel):
    total_gb: float
    used_gb: float
    free_gb: float
    percent_used: float

class ProcessInfo(BaseModel):
    pid: int
    name: str
    username: Optional[str] = None
    cpu_percent: Optional[float] = None
    memory_percent: Optional[float] = None

class ApplicationRequest(BaseModel):
    app_name: str
    args: Optional[List[str]] = []
