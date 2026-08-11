import json
import sys
import subprocess
from langchain.tools import tool

def get_installed_software_data() -> dict:
    """Collect list of installed software applications from Windows Registry."""
    data = {
        "installed_software": [],
        "error": None
    }
    
    if sys.platform != "win32":
        data["error"] = "Software diagnostics are only supported on Windows platforms."
        return data
        
    # Read software registry uninstall locations
    powershell_cmd = (
        'powershell -Command "'
        'Get-ItemProperty HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*, '
        'HKLM:\\Software\\Wow6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*, '
        'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\* '
        '-ErrorAction SilentlyContinue | '
        'Select-Object DisplayName, DisplayVersion, Publisher | '
        'ConvertTo-Json"'
    )
    
    try:
        res = subprocess.run(powershell_cmd, shell=True, capture_output=True, text=True, timeout=15)
        if res.returncode == 0 and res.stdout.strip():
            raw_data = json.loads(res.stdout)
            if isinstance(raw_data, dict):
                raw_data = [raw_data]
                
            seen = set()
            for item in raw_data:
                name = item.get("DisplayName")
                if not name or name.strip() in seen:
                    continue
                seen.add(name.strip())
                
                data["installed_software"].append({
                    "name": name.strip(),
                    "version": (item.get("DisplayVersion") or "Unknown").strip(),
                    "publisher": (item.get("Publisher") or "Unknown").strip()
                })
                
            # Sort alphabetically
            data["installed_software"].sort(key=lambda x: x["name"].lower())
            
        elif res.returncode != 0:
            data["error"] = f"PowerShell returned exit code {res.returncode}. Stderr: {res.stderr}"
    except Exception as e:
        data["error"] = f"Failed to query installed software: {e}"
        
    return data

@tool
def software_diagnostics() -> str:
    """Inspect and list installed software programs, versions, and publishers."""
    data = get_installed_software_data()
    
    if data["error"]:
        return f"⚠ Software Diagnostics: {data['error']}"
        
    apps = data["installed_software"]
    if not apps:
        return "No installed software found in system registry."
        
    lines = []
    lines.append(f"{'Application':<40} {'Version':<20} {'Publisher'}")
    lines.append("-" * 80)
    
    for app in apps[:30]:  # Limit output for LLM context
        pub = app['publisher']
        if len(pub) > 20:
            pub = pub[:17] + "..."
        lines.append(f"{app['name'][:38]:<40} {app['version'][:18]:<20} {pub}")
        
    count = len(apps)
    suffix = f"\n(+ {count - 30} more installed applications)" if count > 30 else ""
    
    return f"INSTALLED SOFTWARE INVENTORY ({count} applications found):\n\n" + "\n".join(lines) + suffix
