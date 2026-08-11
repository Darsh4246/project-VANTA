import json
import sys
import subprocess
from langchain.tools import tool

def get_event_logs_data(days: int = 1) -> dict:
    """Collect error and critical event log statistics from Windows Event Viewer."""
    data = {
        "critical_count": 0,
        "error_count": 0,
        "warning_count": 0,
        "grouped_events": [],
        "error": None
    }
    
    if sys.platform != "win32":
        data["error"] = "Event log diagnostics are only supported on Windows platforms."
        return data
        
    # We run PowerShell to query the count of logs in the last 'days' and group by message/source.
    # Level 1=Critical, 2=Error, 3=Warning.
    # Let's count them individually.
    count_cmd = (
        f'powershell -Command "'
        f'$date = (Get-Date).AddDays(-{days});'
        f'$crit = (Get-WinEvent -FilterHashtable @{{LogName=\'System\',\'Application\'; Level=1; StartTime=$date}} -ErrorAction SilentlyContinue).Count;'
        f'$err = (Get-WinEvent -FilterHashtable @{{LogName=\'System\',\'Application\'; Level=2; StartTime=$date}} -ErrorAction SilentlyContinue).Count;'
        f'$warn = (Get-WinEvent -FilterHashtable @{{LogName=\'System\',\'Application\'; Level=3; StartTime=$date}} -ErrorAction SilentlyContinue).Count;'
        f'[PSCustomObject]@{{Critical=$crit; Error=$err; Warning=$warn}} | ConvertTo-Json"'
    )
    
    # We run another query to get top grouped sources of Errors/Critical logs
    group_cmd = (
        f'powershell -Command "'
        f'$date = (Get-Date).AddDays(-{days});'
        f'Get-WinEvent -FilterHashtable @{{LogName=\'System\',\'Application\'; Level=1,2; StartTime=$date}} -ErrorAction SilentlyContinue | '
        f'Group-Object ProviderName | '
        f'Select-Object Name, Count | '
        f'Sort-Object Count -Descending | '
        f'Select-Object -First 10 | '
        f'ConvertTo-Json"'
    )
    
    try:
        # 1. Fetch counts
        res_count = subprocess.run(count_cmd, shell=True, capture_output=True, text=True, timeout=10)
        if res_count.returncode == 0 and res_count.stdout.strip():
            counts = json.loads(res_count.stdout)
            data["critical_count"] = counts.get("Critical") or 0
            data["error_count"] = counts.get("Error") or 0
            data["warning_count"] = counts.get("Warning") or 0
            
        # 2. Fetch grouped details
        res_group = subprocess.run(group_cmd, shell=True, capture_output=True, text=True, timeout=10)
        if res_group.returncode == 0 and res_group.stdout.strip():
            groups = json.loads(res_group.stdout)
            if isinstance(groups, dict):
                groups = [groups]
            for g in groups:
                data["grouped_events"].append({
                    "provider": g.get("Name"),
                    "count": g.get("Count")
                })
    except Exception as e:
        data["error"] = f"Failed to retrieve event logs: {e}"
        
    return data

@tool
def log_diagnostics(days: int = 1) -> str:
    """Analyze recent Windows system and application event logs. Summarizes critical events, errors, and warnings."""
    data = get_event_logs_data(days)
    
    if data["error"]:
        return f"⚠ Event Log Diagnostics: {data['error']}"
        
    total_issues = data['critical_count'] + data['error_count']
    if total_issues == 0 and data['warning_count'] == 0:
        return f"✓ No errors or warnings found in Windows System/Application logs for the last {days} day(s)."
        
    output = (
        f"EVENT LOG ANALYSIS (Last {days} day(s)):\n"
        f"  Critical Events: {data['critical_count']}\n"
        f"  Error Events:    {data['error_count']}\n"
        f"  Warning Events:  {data['warning_count']}\n\n"
    )
    
    if data["grouped_events"]:
        output += "Top Sources of Critical/Error Events:\n"
        for idx, item in enumerate(data["grouped_events"], 1):
            output += f"  {idx}. Source: {item['provider']} — {item['count']} occurrences\n"
            
    return output
