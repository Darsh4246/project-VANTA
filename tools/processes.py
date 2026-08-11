import psutil
from langchain.tools import tool

def get_processes_data(limit: int = 10) -> dict:
    """Collect lists of processes sorted by CPU and RAM consumption."""
    procs = []
    for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'username']):
        try:
            # We fetch info
            info = p.info
            # CPU percent might be None or need to be divided by CPU count, but we keep raw info
            info['cpu_percent'] = p.cpu_percent()
            procs.append(info)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
            
    # Sort for RAM consumption
    top_ram = sorted(procs, key=lambda x: x['memory_percent'] or 0, reverse=True)[:limit]
    # Sort for CPU consumption
    top_cpu = sorted(procs, key=lambda x: x['cpu_percent'] or 0, reverse=True)[:limit]
    
    # Format processes to hide highly sensitive path names or usernames if safe
    def sanitize(proc_list):
        sanitized = []
        for pr in proc_list:
            sanitized.append({
                "pid": pr['pid'],
                "name": pr['name'],
                "cpu_percent": round(pr['cpu_percent'], 1),
                "memory_percent": round(pr['memory_percent'] or 0.0, 2),
                "username": pr.get('username') or 'N/A'
            })
        return sanitized

    return {
        "top_ram": sanitize(top_ram),
        "top_cpu": sanitize(top_cpu)
    }

@tool
def process_diagnostics(limit: int = 10) -> str:
    """Get active processes consuming the most CPU and RAM resources."""
    data = get_processes_data(limit)
    
    cpu_lines = []
    for i, p in enumerate(data['top_cpu'], 1):
        cpu_lines.append(f"  {i}. {p['name']} (PID {p['pid']}): {p['cpu_percent']}% CPU (Owner: {p['username']})")
        
    ram_lines = []
    for i, p in enumerate(data['top_ram'], 1):
        ram_lines.append(f"  {i}. {p['name']} (PID {p['pid']}): {p['memory_percent']}% RAM (Owner: {p['username']})")
        
    return (
        "TOP CPU CONSUMING PROCESSES:\n" + "\n".join(cpu_lines) + "\n\n"
        "TOP MEMORY CONSUMING PROCESSES:\n" + "\n".join(ram_lines)
    )
