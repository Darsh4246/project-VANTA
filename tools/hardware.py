import subprocess
import sys
import psutil
from langchain.tools import tool

def _run_cmd(cmd: str) -> str:
    """Helper to execute simple commands and return stdout."""
    try:
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
        if res.returncode == 0:
            return res.stdout.strip()
    except Exception:
        pass
    return ""

def get_hardware_data() -> dict:
    """Collect motherboard, CPU model, GPU, battery, and temperatures."""
    data = {
        "motherboard": "Unavailable",
        "cpu_model": "Unavailable",
        "gpu": "Unavailable",
        "battery": None,
        "temperatures": {}
    }
    
    # 1. Motherboard & CPU & GPU via wmic/system commands (Windows-specific)
    if sys.platform == "win32":
        mb_man = _run_cmd("wmic baseboard get Manufacturer /value")
        mb_prod = _run_cmd("wmic baseboard get Product /value")
        # Extract product & manufacturer
        manufacturer = ""
        product = ""
        for line in mb_man.split("\n"):
            if "Manufacturer=" in line:
                manufacturer = line.split("=", 1)[1].strip()
        for line in mb_prod.split("\n"):
            if "Product=" in line:
                product = line.split("=", 1)[1].strip()
        if manufacturer or product:
            data["motherboard"] = f"{manufacturer} {product}".strip()
            
        cpu_name = _run_cmd("wmic cpu get Name /value")
        for line in cpu_name.split("\n"):
            if "Name=" in line:
                data["cpu_model"] = line.split("=", 1)[1].strip()
                
        gpu_name = _run_cmd("wmic path win32_VideoController get Name /value")
        gpus = []
        for line in gpu_name.split("\n"):
            if "Name=" in line:
                gpus.append(line.split("=", 1)[1].strip())
        if gpus:
            data["gpu"] = ", ".join(gpus)
    else:
        # Linux / MacOS fallbacks
        data["motherboard"] = _run_cmd("cat /sys/class/dmi/id/board_name") or "Linux Board"
        data["cpu_model"] = _run_cmd("lscpu | grep 'Model name'") or "Linux CPU"
        data["gpu"] = _run_cmd("lspci | grep -i vga") or "Linux GPU"
        
    # 2. Battery
    try:
        battery = psutil.sensors_battery()
        if battery:
            data["battery"] = {
                "percent": battery.percent,
                "power_plugged": battery.power_plugged,
                "secs_left": battery.secsleft
            }
    except Exception:
        pass
        
    # 3. Temperatures
    # psutil.sensors_temperatures() is not supported natively on Windows psutil.
    # It throws AttributeError or empty dict.
    try:
        temps = psutil.sensors_temperatures()
        if temps:
            for name, entries in temps.items():
                data["temperatures"][name] = [
                    {"label": entry.label or name, "current": entry.current, "high": entry.high, "critical": entry.critical}
                    for entry in entries
                ]
    except Exception:
        pass
        
    return data

@tool
def hardware_diagnostics() -> str:
    """Get description of CPU model, GPU, motherboard, battery health, and system temperatures."""
    data = get_hardware_data()
    
    output = (
        f"Motherboard: {data['motherboard']}\n"
        f"CPU Model: {data['cpu_model']}\n"
        f"GPU: {data['gpu']}\n"
    )
    
    if data['battery']:
        plugged_str = "Plugged in" if data['battery']['power_plugged'] else "Discharging"
        time_str = "Unknown" if data['battery']['secs_left'] in (-1, -2) else f"{int(data['battery']['secs_left'] // 60)} minutes"
        output += f"Battery: {data['battery']['percent']}% ({plugged_str}, Time left: {time_str})\n"
    else:
        output += "Battery: Not detected\n"
        
    if data['temperatures']:
        output += "System Temperatures:\n"
        for name, entries in data['temperatures'].items():
            for entry in entries:
                output += f"  - {entry['label']}: {entry['current']}°C (High warning: {entry['high']}°C, Critical: {entry['critical']}°C)\n"
    else:
        output += "⚠ Hardware temperature unavailable.\nThis hardware/driver does not expose a compatible temperature sensor.\n"
        
    return output
