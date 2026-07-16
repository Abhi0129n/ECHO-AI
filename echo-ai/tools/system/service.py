import os
import sys
import subprocess
import platform
import psutil
from typing import List, Dict, Any, Optional
from tools.system.schemas import (
    CPUInfo,
    MemoryInfo,
    DiskInfo,
    BatteryInfo,
    ProcessInfo
)
from tools.system.utils import bytes_to_gb, validate_app

class SystemService:
    def cpu_usage(self) -> CPUInfo:
        logical_cores = os.cpu_count() or 4
        physical_cores = psutil.cpu_count(logical=False) or (logical_cores // 2 if logical_cores > 1 else 1)
        
        percent = psutil.cpu_percent(interval=0.1)
        freq = psutil.cpu_freq()
        
        return CPUInfo(
            percent_usage=percent,
            cores_physical=physical_cores,
            cores_logical=logical_cores,
            frequency_mhz=freq.current if freq else None
        )

    def memory_usage(self) -> MemoryInfo:
        mem = psutil.virtual_memory()
        return MemoryInfo(
            total_gb=bytes_to_gb(mem.total),
            available_gb=bytes_to_gb(mem.available),
            used_gb=bytes_to_gb(mem.used),
            percent_used=mem.percent
        )

    def disk_usage(self, path: Optional[str] = None) -> DiskInfo:
        if not path:
            path = "C:\\" if platform.system() == "Windows" else "/"
            
        usage = psutil.disk_usage(path)
        return DiskInfo(
            total_gb=bytes_to_gb(usage.total),
            used_gb=bytes_to_gb(usage.used),
            free_gb=bytes_to_gb(usage.free),
            percent_used=usage.percent
        )

    def battery_status(self) -> BatteryInfo:
        battery = psutil.sensors_battery()
        if battery:
            return BatteryInfo(
                percent=battery.percent,
                power_plugged=battery.power_plugged,
                secs_left=battery.secsleft if battery.secsleft != -1 and battery.secsleft != -2 else None
            )
        # Mock fallback if no battery exists (e.g. desktop)
        return BatteryInfo(percent=100.0, power_plugged=True, secs_left=None)

    def list_processes(self, limit: int = 20) -> List[ProcessInfo]:
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent']):
            try:
                info = proc.info
                processes.append(ProcessInfo(
                    pid=info['pid'],
                    name=info['name'] or "Unknown",
                    username=info['username'],
                    cpu_percent=info['cpu_percent'],
                    memory_percent=info['memory_percent']
                ))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        # Sort by memory usage descending
        processes.sort(key=lambda x: x.memory_percent or 0, reverse=True)
        return processes[:limit]

    def get_installed_applications(self) -> List[str]:
        apps = []
        if platform.system() == "Windows":
            try:
                import winreg
                reg_paths = [
                    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
                    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
                    (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Uninstall")
                ]
                for hive, path in reg_paths:
                    try:
                        with winreg.OpenKey(hive, path) as key:
                            num_subkeys = winreg.QueryInfoKey(key)[0]
                            for i in range(num_subkeys):
                                try:
                                    subkey_name = winreg.EnumKey(key, i)
                                    with winreg.OpenKey(key, subkey_name) as subkey:
                                        try:
                                            name, _ = winreg.QueryValueEx(subkey, "DisplayName")
                                            if name and name not in apps:
                                                apps.append(name)
                                        except OSError:
                                            pass
                                except OSError:
                                    continue
                    except OSError:
                        continue
            except ImportError:
                pass
        elif platform.system() == "Darwin":
            # macOS best effort
            for app_dir in ["/Applications", os.path.expanduser("~/Applications")]:
                if os.path.exists(app_dir):
                    for item in os.listdir(app_dir):
                        if item.endswith(".app"):
                            apps.append(item[:-4])
        else:
            # Linux best effort
            applications_dir = "/usr/share/applications"
            if os.path.exists(applications_dir):
                for item in os.listdir(applications_dir):
                    if item.endswith(".desktop"):
                        apps.append(item[:-8])
        return sorted(apps)

    def open_application(self, app_name: str, args: List[str] = None) -> Dict[str, Any]:
        if not validate_app(app_name):
            raise ValueError(f"Application name or path '{app_name}' contains illegal characters")
            
        cmd = [app_name] + (args or [])
        # Launch process without blocking
        process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return {
            "status": "success",
            "pid": process.pid,
            "app_name": app_name,
            "args": args or []
        }

    def close_application(self, app_name: str) -> Dict[str, Any]:
        if not validate_app(app_name):
            raise ValueError(f"Application name '{app_name}' contains illegal characters")
            
        terminated_count = 0
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.info['name'] and app_name.lower() in proc.info['name'].lower():
                    proc.terminate()
                    terminated_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return {
            "status": "success",
            "terminated_count": terminated_count,
            "app_name": app_name
        }
