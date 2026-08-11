import json
import sys
import subprocess
from langchain.tools import tool

def get_services_data() -> dict:
    """Find Windows services configured to run automatically that are stopped or failed."""
    data = {
        "stopped_auto_services": [],
        "error": None
    }
    
    if sys.platform != "win32":
        data["error"] = "Service diagnostics are only supported on Windows platforms."
        return data
        
    # Query services configured as Auto but not Running
    cmd = 'powershell -Command "Get-CimInstance -ClassName Win32_Service | Where-Object { $_.StartMode -eq \'Auto\' -and $_.State -ne \'Running\' } | Select-Object Name, DisplayName, State, StartMode | ConvertTo-Json"'
    try:
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        if res.returncode == 0 and res.stdout.strip():
            raw_data = json.loads(res.stdout)
            # PowerShell ConvertTo-Json returns a single dict if there is only 1 item, or a list if multiple.
            if isinstance(raw_data, dict):
                raw_data = [raw_data]
            
            for item in raw_data:
                data["stopped_auto_services"].append({
                    "name": item.get("Name"),
                    "display_name": item.get("DisplayName"),
                    "state": item.get("State"),
                    "start_mode": item.get("StartMode")
                })
        elif res.returncode != 0:
            data["error"] = f"PowerShell returned exit code {res.returncode}. Stderr: {res.stderr}"
    except Exception as e:
        data["error"] = f"Failed to execute service query: {e}"
        
    return data

@tool
def service_diagnostics() -> str:
    """Inspect stopped or failed Windows services that are configured to start automatically."""
    data = get_services_data()
    
    if data["error"]:
        return f"⚠ Service Diagnostics: {data['error']}"
        
    services = data["stopped_auto_services"]
    if not services:
        return "✓ All services configured for automatic startup are running successfully."
        
    lines = []
    for s in services[:30]:  # Limit output length for agent context
        lines.append(f"  - {s['display_name']} ({s['name']}): State={s['state']}")
        
    count = len(services)
    suffix = f"\n(+ {count - 30} more stopped services)" if count > 30 else ""
    
    return f"Stopped Automatic Startup Services ({count} found):\n" + "\n".join(lines) + suffix
