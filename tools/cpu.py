import psutil
from langchain.tools import tool

def get_cpu_data() -> dict:
    """Collect raw CPU usage and frequency metrics."""
    cpu_percent = psutil.cpu_percent(interval=0.2)
    per_cpu_percent = psutil.cpu_percent(interval=0.2, percpu=True)
    
    # CPU Frequency
    try:
        freq = psutil.cpu_freq()
        current_freq = freq.current if freq else 0.0
        min_freq = freq.min if freq else 0.0
        max_freq = freq.max if freq else 0.0
    except Exception:
        current_freq = min_freq = max_freq = 0.0
        
    logical_cores = psutil.cpu_count(logical=True) or 0
    physical_cores = psutil.cpu_count(logical=False) or 0
    
    # Load averages (not natively supported on Windows via psutil, so check platform)
    load_avg = [0.0, 0.0, 0.0]
    import sys
    if sys.platform != "win32":
        try:
            load_avg = list(psutil.getloadavg())
        except Exception:
            pass

    return {
        "cpu_percent": cpu_percent,
        "per_cpu_percent": per_cpu_percent,
        "frequency_current_mhz": round(current_freq, 1),
        "frequency_min_mhz": round(min_freq, 1),
        "frequency_max_mhz": round(max_freq, 1),
        "logical_cores": logical_cores,
        "physical_cores": physical_cores,
        "load_avg": load_avg
    }

@tool
def cpu_diagnostics() -> str:
    """Get active CPU usage stats including load percent, per-core utilization, and core counts."""
    data = get_cpu_data()
    per_core_str = ", ".join(f"Core {i}: {p}%" for i, p in enumerate(data['per_cpu_percent']))
    
    output = (
        f"Overall CPU Usage: {data['cpu_percent']}%\n"
        f"Logical Cores: {data['logical_cores']} | Physical Cores: {data['physical_cores']}\n"
        f"Frequency: {data['frequency_current_mhz']} MHz"
    )
    if data['frequency_max_mhz']:
        output += f" (Max: {data['frequency_max_mhz']} MHz, Min: {data['frequency_min_mhz']} MHz)"
    output += f"\nPer-Core Usage: {per_core_str}\n"
    
    if any(data['load_avg']):
        output += f"Load Average (1m, 5m, 15m): {data['load_avg']}\n"
        
    return output
