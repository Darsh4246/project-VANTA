import json
import sys
import subprocess
from langchain.tools import tool

def _run_ps_json(cmd: str) -> list:
    """Run a PowerShell command and parse the JSON output."""
    try:
        res = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, text=True, timeout=15)
        if res.returncode == 0 and res.stdout.strip():
            try:
                parsed = json.loads(res.stdout)
                if isinstance(parsed, dict):
                    return [parsed]
                elif isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                pass
    except Exception:
        pass
    return []

def get_device_driver_data(filter_class: str = None, query: str = None, show_problematic_only: bool = False) -> dict:
    """Collect Plug & Play devices and system driver diagnostics."""
    data = {
        "platform": sys.platform,
        "devices": [],
        "drivers": [],
        "class_summary": [],
        "biometric_devices": [],
        "problematic_devices": [],
        "error": None
    }
    
    if sys.platform != "win32":
        # Fallback for non-Windows platforms
        try:
            # Let's check for lspci/lsusb
            devices_info = []
            lspci_res = subprocess.run("lspci", shell=True, capture_output=True, text=True, timeout=5)
            if lspci_res.returncode == 0:
                devices_info.append("--- PCI Devices ---")
                devices_info.append(lspci_res.stdout.strip())
            lsusb_res = subprocess.run("lsusb", shell=True, capture_output=True, text=True, timeout=5)
            if lsusb_res.returncode == 0:
                devices_info.append("--- USB Devices ---")
                devices_info.append(lsusb_res.stdout.strip())
                
            combined = "\n".join(devices_info)
            if query:
                filtered = [line for line in combined.split("\n") if query.lower() in line.lower()]
                data["devices"] = [{"FriendlyName": line, "Status": "OK", "Class": "Unknown"} for line in filtered]
            else:
                # Provide a limited set
                data["devices"] = [{"FriendlyName": line, "Status": "OK", "Class": "Unknown"} for line in combined.split("\n")[:30]]
        except Exception as e:
            data["error"] = f"Failed to retrieve non-Windows devices: {e}"
        return data

    # Windows platform logic
    try:
        if show_problematic_only:
            # Get ERROR/DEGRADED devices
            prob_cmd = "Get-PnpDevice -Status ERROR, DEGRADED -ErrorAction SilentlyContinue | Select-Object FriendlyName, Class, Status, InstanceId | ConvertTo-Json"
            data["problematic_devices"] = _run_ps_json(prob_cmd)
            
        elif filter_class:
            # Filter PnP devices by class
            class_sanitized = filter_class.replace("'", "''")
            cmd = f"Get-PnpDevice -Class '{class_sanitized}' -ErrorAction SilentlyContinue | Select-Object FriendlyName, Status, Manufacturer, Class, InstanceId | ConvertTo-Json"
            data["devices"] = _run_ps_json(cmd)
            
        elif query:
            # Filter PnP devices and system drivers by query
            query_sanitized = query.replace("'", "''")
            dev_cmd = f"Get-PnpDevice -ErrorAction SilentlyContinue | Where-Object {{ $_.FriendlyName -like '*{query_sanitized}*' -or $_.Manufacturer -like '*{query_sanitized}*' -or $_.Class -like '*{query_sanitized}*' }} | Select-Object FriendlyName, Status, Manufacturer, Class, InstanceId | ConvertTo-Json"
            data["devices"] = _run_ps_json(dev_cmd)
            
            drv_cmd = f"Get-CimInstance Win32_SystemDriver -ErrorAction SilentlyContinue | Where-Object {{ $_.Name -like '*{query_sanitized}*' -or $_.DisplayName -like '*{query_sanitized}*' }} | Select-Object Name, DisplayName, State, Status, StartMode, ServiceType | ConvertTo-Json"
            data["drivers"] = _run_ps_json(drv_cmd)
            
        else:
            # Default summary view:
            # 1. Device classes counts
            summary_cmd = "Get-PnpDevice -ErrorAction SilentlyContinue | Group-Object Class | Select-Object Name, Count | ConvertTo-Json"
            data["class_summary"] = _run_ps_json(summary_cmd)
            
            # 2. Biometric devices
            biometric_cmd = "Get-PnpDevice -Class Biometric -ErrorAction SilentlyContinue | Select-Object FriendlyName, Status, Manufacturer, Class, InstanceId | ConvertTo-Json"
            data["biometric_devices"] = _run_ps_json(biometric_cmd)
            
            # 3. Problematic devices
            prob_cmd = "Get-PnpDevice -Status ERROR, DEGRADED -ErrorAction SilentlyContinue | Select-Object FriendlyName, Class, Status, InstanceId | ConvertTo-Json"
            data["problematic_devices"] = _run_ps_json(prob_cmd)
            
    except Exception as e:
        data["error"] = f"Failed to retrieve Windows devices/drivers: {e}"
        
    return data

@tool
def device_driver_diagnostics(filter_class: str = None, query: str = None, show_problematic_only: bool = False) -> str:
    """Inspect and analyze system devices (Plug and Play) and active drivers.
    
    Can filter by device class (e.g. 'Biometric', 'USB', 'Display', 'Net'), search for a query string in device/driver names, or display problematic devices (errors/warnings/degraded status).
    """
    data = get_device_driver_data(filter_class, query, show_problematic_only)
    
    if data["error"]:
        return f"⚠ Device & Driver Diagnostics: {data['error']}"
        
    output = []
    
    if show_problematic_only:
        prob = data["problematic_devices"]
        if not prob:
            return "✓ No problematic devices (ERROR or DEGRADED status) found on the system."
        output.append(f"PROBLEMATIC DEVICES FOUND ({len(prob)} devices):")
        for d in prob:
            output.append(f"  - [{d.get('Status', 'UNKNOWN')}] {d.get('FriendlyName', 'Unknown')} (Class: {d.get('Class', 'Unknown')})")
            output.append(f"    Instance ID: {d.get('InstanceId', 'N/A')}")
        return "\n".join(output)
        
    if filter_class:
        devs = data["devices"]
        if not devs:
            return f"No devices found in class '{filter_class}'."
        output.append(f"DEVICES IN CLASS '{filter_class}' ({len(devs)} found):")
        for d in devs[:30]:  # Limit output context size
            output.append(f"  - {d.get('FriendlyName', 'Unknown')} | Status: {d.get('Status', 'Unknown')} | Manufacturer: {d.get('Manufacturer', 'Unknown')}")
        if len(devs) > 30:
            output.append(f"  (+ {len(devs) - 30} more devices in this class)")
        return "\n".join(output)
        
    if query:
        devs = data["devices"]
        drvs = data["drivers"]
        if not devs and not drvs:
            return f"No devices or drivers found matching search query: '{query}'."
            
        if devs:
            output.append(f"MATCHING DEVICES ({len(devs)} found):")
            for d in devs[:20]:
                output.append(f"  - {d.get('FriendlyName', 'Unknown')} (Class: {d.get('Class', 'Unknown')}) | Status: {d.get('Status', 'Unknown')} | Manufacturer: {d.get('Manufacturer', 'Unknown')}")
            if len(devs) > 20:
                output.append(f"  (+ {len(devs) - 20} more matching devices)")
            output.append("")
            
        if drvs:
            output.append(f"MATCHING SYSTEM DRIVERS ({len(drvs)} found):")
            for d in drvs[:20]:
                output.append(f"  - {d.get('DisplayName', 'Unknown')} ({d.get('Name', 'Unknown')}) | State: {d.get('State', 'Unknown')} | StartMode: {d.get('StartMode', 'Unknown')}")
            if len(drvs) > 20:
                output.append(f"  (+ {len(drvs) - 20} more matching drivers)")
                
        return "\n".join(output).strip()
        
    # Default general view
    if sys.platform != "win32":
        devs = data["devices"]
        output.append(f"SYSTEM DEVICES INVENTORY ({len(devs)} listed):")
        for d in devs:
            output.append(f"  - {d.get('FriendlyName')}")
        return "\n".join(output)
        
    # Windows default summary
    output.append("SYSTEM DEVICE AND DRIVER DIAGNOSTICS SUMMARY:\n")
    
    biometric = data["biometric_devices"]
    if biometric:
        output.append(f"Biometric Devices ({len(biometric)} found):")
        for d in biometric:
            output.append(f"  - {d.get('FriendlyName', 'Unknown')} | Manufacturer: {d.get('Manufacturer', 'Unknown')} | Status: {d.get('Status', 'Unknown')}")
            output.append(f"    Instance ID: {d.get('InstanceId', 'N/A')}")
        output.append("")
    else:
        output.append("Biometric Devices: None detected (e.g. no active fingerprint reader or camera driver registered as Biometric).\n")
        
    prob = data["problematic_devices"]
    if prob:
        output.append(f"⚠ Problematic Devices ({len(prob)} found with non-OK status):")
        for d in prob:
            output.append(f"  - [{d.get('Status', 'UNKNOWN')}] {d.get('FriendlyName', 'Unknown')} (Class: {d.get('Class', 'Unknown')})")
        output.append("")
    else:
        output.append("✓ Device Status Check: All active system devices are running normally (no ERROR or DEGRADED status detected).\n")
        
    summary = data["class_summary"]
    if summary:
        output.append("Device Class Distribution:")
        # Sort classes by count descending
        sorted_summary = sorted(summary, key=lambda x: x.get("Count", 0), reverse=True)
        for c in sorted_summary[:15]:
            name = c.get("Name") or "Unclassified"
            output.append(f"  - {name:<25} : {c.get('Count', 0)} devices")
        if len(sorted_summary) > 15:
            output.append(f"  (+ {len(sorted_summary) - 15} other device classes)")
            
    return "\n".join(output)
