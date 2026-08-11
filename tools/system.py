import os
import sys
import platform
import time
import psutil
from langchain.tools import tool

def get_system_info_data() -> dict:
    """Collect raw system info data."""
    # Uptime calculation
    boot_time = psutil.boot_time()
    uptime_seconds = time.time() - boot_time
    hours = int(uptime_seconds // 3600)
    minutes = int((uptime_seconds % 3600) // 60)
    
    # RAM / Memory
    mem = psutil.virtual_memory()
    
    # Disk (Root drive)
    root_dir = os.path.abspath(os.sep)
    try:
        disk = psutil.disk_usage(root_dir)
        disk_total = disk.total
        disk_used = disk.used
        disk_free = disk.free
        disk_percent = disk.percent
    except Exception:
        disk_total = disk_used = disk_free = disk_percent = 0

    return {
        "os_name": os.name,
        "platform": platform.system(),
        "platform_release": platform.release(),
        "platform_version": platform.version(),
        "architecture": platform.machine(),
        "hostname": platform.node(),
        "processor": platform.processor(),
        "cpu_cores": psutil.cpu_count(logical=True),
        "cpu_physical_cores": psutil.cpu_count(logical=False),
        "ram_total_gb": round(mem.total / (1024**3), 2),
        "ram_used_gb": round(mem.used / (1024**3), 2),
        "ram_free_gb": round(mem.available / (1024**3), 2),
        "ram_percent": mem.percent,
        "disk_total_gb": round(disk_total / (1024**3), 2),
        "disk_used_gb": round(disk_used / (1024**3), 2),
        "disk_free_gb": round(disk_free / (1024**3), 2),
        "disk_percent": disk_percent,
        "uptime_str": f"{hours}h {minutes}m",
        "uptime_seconds": uptime_seconds,
        "python_version": sys.version.split()[0]
    }

@tool
def system_info() -> str:
    """Get current operating system description, hostname, uptime, architecture, and overall resource summary."""
    data = get_system_info_data()
    return (
        f"OS: {data['platform']} {data['platform_release']} (Version: {data['platform_version']})\n"
        f"Hostname: {data['hostname']}\n"
        f"Architecture: {data['architecture']}\n"
        f"Uptime: {data['uptime_str']}\n"
        f"Python Version: {data['python_version']}\n"
        f"CPU Cores: {data['cpu_cores']} logical ({data['cpu_physical_cores']} physical)\n"
        f"RAM: {data['ram_used_gb']} GB / {data['ram_total_gb']} GB ({data['ram_percent']}%)\n"
        f"Disk (System Drive): {data['disk_used_gb']} GB / {data['disk_total_gb']} GB ({data['disk_percent']}%)\n"
    )
