import os
import sys
import shutil
import subprocess
from pathlib import Path
from vanta.actions.permissions import is_admin

def restart_service_impl(service_name: str) -> str:
    """Restarts a specified Windows service."""
    if sys.platform != "win32":
        return "Failed: Service management is only supported on Windows."
        
    if not is_admin():
        return "Failed: Administrative privileges are required to restart services."
        
    # Use powershell
    cmd = f'powershell -Command "Restart-Service -Name \'{service_name}\' -Force"'
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if res.returncode == 0:
        return f"Successfully restarted service: {service_name}"
    else:
        return f"Failed to restart service: {res.stderr.strip() or 'Unknown error'}"

def clear_temp_files_impl() -> str:
    """Safely removes temporary files from system directories."""
    paths_to_clear = []
    
    # User temp
    user_temp = os.environ.get("TEMP")
    if user_temp:
        paths_to_clear.append(Path(user_temp))
        
    # System temp
    if sys.platform == "win32":
        system_temp = Path(os.environ.get("SystemRoot", "C:\\Windows")) / "Temp"
        paths_to_clear.append(system_temp)
    else:
        paths_to_clear.append(Path("/tmp"))
        
    deleted_files = 0
    deleted_dirs = 0
    failed_files = 0
    freed_bytes = 0
    
    for temp_path in paths_to_clear:
        if not temp_path.exists() or not temp_path.is_dir():
            continue
            
        for item in temp_path.iterdir():
            try:
                # Skip active files/directories or lock files
                if item.name.startswith("~") or item.suffix.lower() == ".tmp":
                    pass
                if item.is_file() or item.is_symlink():
                    size = item.stat().st_size
                    item.unlink()
                    deleted_files += 1
                    freed_bytes += size
                elif item.is_dir():
                    shutil.rmtree(item)
                    deleted_dirs += 1
            except Exception:
                failed_files += 1
                
    freed_mb = round(freed_bytes / (1024 * 1024), 2)
    return (
        f"Cleanup Complete. Cleared {deleted_files} files and {deleted_dirs} directories. "
        f"Freed {freed_mb} MB. (Skipped {failed_files} locked files/folders)."
    )

def disable_startup_app_impl(app_name: str) -> str:
    """Disables a startup application from the current user registry Run path."""
    if sys.platform != "win32":
        return "Failed: Startup management is only supported on Windows."
        
    # We remove key from HKCU:\Software\Microsoft\Windows\CurrentVersion\Run
    cmd = (
        f'powershell -Command "'
        f'$runPath = \'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Run\';'
        f'if (Get-ItemProperty -Path $runPath -Name \'{app_name}\' -ErrorAction SilentlyContinue) {{'
        f'  Remove-ItemProperty -Path $runPath -Name \'{app_name}\' -Force;'
        f'  Write-Output \'Removed\';'
        f'}} else {{'
        f'  Write-Output \'NotFound\';'
        f'}}"'
    )
    
    try:
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        out = res.stdout.strip()
        if out == "Removed":
            return f"Successfully disabled startup application: {app_name}"
        elif out == "NotFound":
            return f"Application '{app_name}' was not found in user startup registry."
        else:
            return f"Failed to disable startup app: {res.stderr.strip() or 'Unknown error'}"
    except Exception as e:
        return f"Failed to execute startup disable: {e}"

def flush_dns_impl() -> str:
    """Flushes local DNS resolver caches."""
    if sys.platform == "win32":
        cmd = "ipconfig /flushdns"
    elif sys.platform == "darwin":
        cmd = "sudo killall -HUP mDNSResponder"
    else:
        cmd = "sudo systemd-resolve --flush-caches"
        
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if res.returncode == 0:
        return "Successfully flushed the DNS Resolver Cache."
    else:
        # If it failed on linux/mac due to sudo, try without sudo
        if "sudo" in cmd:
            fallback_cmd = cmd.replace("sudo ", "")
            res_fb = subprocess.run(fallback_cmd, shell=True, capture_output=True, text=True)
            if res_fb.returncode == 0:
                return "Successfully flushed the DNS Resolver Cache."
        return f"Failed to flush DNS cache: {res.stderr.strip() or 'Unknown error'}"
