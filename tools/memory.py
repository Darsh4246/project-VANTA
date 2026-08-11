import psutil
from langchain.tools import tool

def get_memory_data() -> dict:
    """Collect raw virtual and swap memory metrics."""
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()
    
    return {
        "ram_total_gb": round(mem.total / (1024**3), 2),
        "ram_used_gb": round(mem.used / (1024**3), 2),
        "ram_available_gb": round(mem.available / (1024**3), 2),
        "ram_percent": mem.percent,
        "swap_total_gb": round(swap.total / (1024**3), 2),
        "swap_used_gb": round(swap.used / (1024**3), 2),
        "swap_free_gb": round(swap.free / (1024**3), 2),
        "swap_percent": swap.percent
    }

@tool
def memory_diagnostics() -> str:
    """Get active RAM and swap memory usage metrics, available capacity, and percentages."""
    data = get_memory_data()
    return (
        f"RAM Total: {data['ram_total_gb']} GB\n"
        f"RAM Used: {data['ram_used_gb']} GB ({data['ram_percent']}%)\n"
        f"RAM Available: {data['ram_available_gb']} GB\n"
        f"Swap/Pagefile Total: {data['swap_total_gb']} GB\n"
        f"Swap/Pagefile Used: {data['swap_used_gb']} GB ({data['swap_percent']}%)\n"
        f"Swap/Pagefile Free: {data['swap_free_gb']} GB\n"
    )
