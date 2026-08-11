import socket
import time
import sys
import subprocess
import psutil
from langchain.tools import tool

def _run_cmd(cmd: str) -> str:
    try:
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
        if res.returncode == 0:
            return res.stdout.strip()
    except Exception:
        pass
    return ""

def get_network_data() -> dict:
    """Run connection diagnostics and collect gateway, DNS, and latency stats."""
    data = {
        "adapters": [],
        "local_ip": "Unknown",
        "gateway": "Unknown",
        "dns_servers": [],
        "gateway_reachable": False,
        "dns_resolvable": False,
        "internet_reachable": False,
        "dns_resolution_time_ms": 0.0,
        "latency_ms": 0.0
    }
    
    # 1. Local IP & Interfaces
    try:
        for interface_name, addresses in psutil.net_if_addrs().items():
            for addr in addresses:
                if addr.family == socket.AF_INET and not addr.address.startswith("127."):
                    data["local_ip"] = addr.address
                    data["adapters"].append({
                        "interface": interface_name,
                        "ip": addr.address,
                        "netmask": addr.netmask
                    })
    except Exception:
        pass

    # 2. Gateway and DNS (Windows specific / Platform specific)
    if sys.platform == "win32":
        # Extract default gateway via powershell
        gw_out = _run_cmd("powershell -Command \"(Get-NetRoute -DestinationPrefix '0.0.0.0/0' | Select-Object -First 1).NextHop\"")
        if gw_out:
            data["gateway"] = gw_out
            
        # Extract DNS servers via powershell
        dns_out = _run_cmd("powershell -Command \"(Get-DnsClientServerAddress -AddressFamily IPv4 | Select-Object -ExpandProperty ServerAddresses) -join ', '\"")
        if dns_out:
            data["dns_servers"] = [d.strip() for d in dns_out.split(",") if d.strip()]
    else:
        # Linux fallback
        # Gateway
        gw_out = _run_cmd("ip route show | grep default | awk '{print $3}'")
        if gw_out:
            data["gateway"] = gw_out
        # DNS
        try:
            with open("/etc/resolv.conf", "r") as f:
                for line in f:
                    if line.startswith("nameserver"):
                        data["dns_servers"].append(line.split()[1])
        except Exception:
            pass

    # 3. Connectivity diagnostics
    # Test 3a: Gateway Reachability (Ping gateway)
    if data["gateway"] != "Unknown":
        ping_cmd = f"ping -n 1 -w 1000 {data['gateway']}" if sys.platform == "win32" else f"ping -c 1 -W 1 {data['gateway']}"
        res = subprocess.run(ping_cmd, shell=True, capture_output=True, text=True)
        data["gateway_reachable"] = (res.returncode == 0)
        
    # Test 3b: DNS Resolvability & internet connectivity
    # Resolve google.com and track response time
    t0 = time.perf_counter()
    try:
        socket.gethostbyname("google.com")
        dns_resolution_time = (time.perf_counter() - t0) * 1000
        data["dns_resolvable"] = True
        data["dns_resolution_time_ms"] = round(dns_resolution_time, 2)
    except socket.gaierror:
        data["dns_resolvable"] = False
        
    # Test 3c: Ping an external host (8.8.8.8) to check latency and internet connection
    ping_ext_cmd = "ping -n 3 8.8.8.8" if sys.platform == "win32" else "ping -c 3 8.8.8.8"
    try:
        ping_res = subprocess.run(ping_ext_cmd, shell=True, capture_output=True, text=True, timeout=5)
        if ping_res.returncode == 0:
            data["internet_reachable"] = True
            # Extract latency on Windows
            if sys.platform == "win32":
                lines = ping_res.stdout.splitlines()
                for line in lines:
                    if "Average =" in line:
                        parts = line.split("Average =")
                        if len(parts) > 1:
                            lat = parts[1].replace("ms", "").strip()
                            data["latency_ms"] = float(lat)
            else:
                # Linux extraction
                last_line = ping_res.stdout.strip().split("\n")[-1]
                if "rtt" in last_line:
                    avg_val = last_line.split("/")[4]
                    data["latency_ms"] = float(avg_val)
    except Exception:
        pass
        
    return data

@tool
def network_diagnostics() -> str:
    """Run connection diagnostics: adapters, local IP, gateway, DNS servers, and latency to external servers."""
    data = get_network_data()
    
    adapters_str = "\n".join(f"  - Interface '{a['interface']}': IP={a['ip']}, Mask={a['netmask']}" for a in data['adapters'])
    dns_servers_str = ", ".join(data['dns_servers']) if data['dns_servers'] else "None detected"
    
    status_gw = "Reachable" if data['gateway_reachable'] else "UNREACHABLE"
    status_dns = f"Operational (Resolution time: {data['dns_resolution_time_ms']} ms)" if data['dns_resolvable'] else "FAILED"
    status_internet = f"Connected (Avg Latency: {data['latency_ms']} ms)" if data['internet_reachable'] else "DISCONNECTED"
    
    return (
        f"NETWORK ADAPTERS:\n{adapters_str}\n\n"
        f"Local IP: {data['local_ip']}\n"
        f"Default Gateway: {data['gateway']} ({status_gw})\n"
        f"DNS Servers: {dns_servers_str}\n"
        f"DNS Resolution: {status_dns}\n"
        f"Internet Connectivity: {status_internet}\n"
    )
