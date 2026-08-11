import psutil
from langchain.tools import tool

def get_storage_data() -> dict:
    """Collect partition statistics and detect space threshold warnings."""
    partitions = []
    warnings = []
    
    for part in psutil.disk_partitions(all=False):
        # Exclude loopback or CD-ROM etc.
        if 'cdrom' in part.opts or not part.fstype:
            continue
        try:
            usage = psutil.disk_usage(part.mountpoint)
            free_pct = (usage.free / usage.total) * 100
            
            status = "HEALTHY"
            if free_pct < 5:
                status = "CRITICAL"
                warnings.append(f"Drive {part.mountpoint} is CRITICAL (less than 5% free space: {free_pct:.1f}% free)")
            elif free_pct < 10:
                status = "WARNING"
                warnings.append(f"Drive {part.mountpoint} is WARNING (less than 10% free space: {free_pct:.1f}% free)")
                
            partitions.append({
                "device": part.device,
                "mountpoint": part.mountpoint,
                "fstype": part.fstype,
                "total_gb": round(usage.total / (1024**3), 2),
                "used_gb": round(usage.used / (1024**3), 2),
                "free_gb": round(usage.free / (1024**3), 2),
                "percent_used": usage.percent,
                "percent_free": round(free_pct, 2),
                "status": status
            })
        except Exception:
            pass
            
    return {
        "partitions": partitions,
        "warnings": warnings
    }

@tool
def storage_diagnostics() -> str:
    """Get active storage disk/partition information, including filesystem types, capacities, free space, and warnings."""
    data = get_storage_data()
    
    lines = []
    for p in data['partitions']:
        lines.append(
            f"Drive: {p['mountpoint']} ({p['device']}) | FS: {p['fstype']} | Status: {p['status']}\n"
            f"  Total: {p['total_gb']} GB | Used: {p['used_gb']} GB ({p['percent_used']}% used) | Free: {p['free_gb']} GB ({p['percent_free']}% free)"
        )
        
    warnings_str = ""
    if data['warnings']:
        warnings_str = "\n⚠ STORAGE WARNINGS:\n" + "\n".join(f"  - {w}" for w in data['warnings']) + "\n"
        
    return "STORAGE DRIVES AND PARTITIONS:\n" + "\n\n".join(lines) + warnings_str
