import json
import sys
import subprocess
from langchain.tools import tool

# Common startup apps and their estimated boot impact
IMPACT_REGISTRY = {
    "discord": "HIGH",
    "steam": "HIGH",
    "spotify": "HIGH",
    "onedrive": "MEDIUM",
    "dropbox": "MEDIUM",
    "teams": "HIGH",
    "slack": "HIGH",
    "chrome": "HIGH",
    "skype": "HIGH",
    "utorrent": "HIGH",
    "bittorrent": "HIGH",
    "adobe": "MEDIUM",
    "cortana": "LOW",
    "epicgames": "HIGH",
    "gog": "HIGH"
}

def get_startup_data() -> dict:
    """List startup applications and estimate their impact."""
    data = {
        "startup_items": [],
        "error": None
    }
    
    if sys.platform != "win32":
        data["error"] = "Startup diagnostics are only supported on Windows platforms."
        return data
        
    cmd = 'powershell -Command "Get-CimInstance -ClassName Win32_StartupCommand | Select-Object Name, Command, Location, User | ConvertTo-Json"'
    try:
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        if res.returncode == 0 and res.stdout.strip():
            raw_data = json.loads(res.stdout)
            if isinstance(raw_data, dict):
                raw_data = [raw_data]
                
            for item in raw_data:
                name = item.get("Name", "Unknown")
                command = item.get("Command", "")
                
                # Deduce impact level
                name_lower = name.lower()
                cmd_lower = command.lower()
                
                impact = "LOW"
                for keyword, level in IMPACT_REGISTRY.items():
                    if keyword in name_lower or keyword in cmd_lower:
                        impact = level
                        break
                        
                data["startup_items"].append({
                    "name": name,
                    "command": command,
                    "location": item.get("Location", ""),
                    "user": item.get("User", ""),
                    "impact": impact
                })
        elif res.returncode != 0:
            data["error"] = f"PowerShell returned exit code {res.returncode}. Stderr: {res.stderr}"
    except Exception as e:
        data["error"] = f"Failed to execute startup query: {e}"
        
    return data

@tool
def startup_diagnostics() -> str:
    """Inspect and list applications that launch automatically on system startup, with estimated boot impacts."""
    data = get_startup_data()
    
    if data["error"]:
        return f"⚠ Startup Diagnostics: {data['error']}"
        
    items = data["startup_items"]
    if not items:
        return "No startup applications found."
        
    lines = []
    # Print layout
    lines.append(f"{'Application':<25} {'Impact':<10} {'Command'}")
    lines.append("-" * 65)
    
    for item in items[:25]:
        cmd_snippet = item['command']
        if len(cmd_snippet) > 40:
            cmd_snippet = cmd_snippet[:37] + "..."
        lines.append(f"{item['name']:<25} {item['impact']:<10} {cmd_snippet}")
        
    count = len(items)
    suffix = f"\n(+ {count - 25} more startup applications)" if count > 25 else ""
    
    # Calculate potential optimization count
    opt_count = sum(1 for item in items if item['impact'] in ("HIGH", "MEDIUM"))
    optimization_info = f"\nPotential optimization: {opt_count} applications could be disabled from startup to speed up boot time.\n"
    
    return "STARTUP APPLICATIONS ANALYSIS:\n\n" + "\n".join(lines) + suffix + "\n" + optimization_info
