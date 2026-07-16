from pydantic import BaseModel, Field
from typing import Optional, List, Dict

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

class BatteryInfo(BaseModel):
    percent: float
    power_plugged: Optional[bool] = None
    secs_left: Optional[int] = None

class ProcessInfo(BaseModel):
    pid: int
    name: str
    username: Optional[str] = None
    cpu_percent: Optional[float] = None
    memory_percent: Optional[float] = None

class OpenAppRequest(BaseModel):
    app_name: str = Field(..., description="Name or path of the application to open")
    args: List[str] = Field(default_factory=list, description="Arguments to pass to the application")

class CloseAppRequest(BaseModel):
    app_name: str = Field(..., description="Name of the application/process to close")
