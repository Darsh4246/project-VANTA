import sys
from vanta.tools.cpu import get_cpu_data
from vanta.tools.memory import get_memory_data
from vanta.tools.storage import get_storage_data
from vanta.tools.network import get_network_data
from vanta.tools.services import get_services_data
from vanta.tools.startup import get_startup_data
from vanta.tools.logs import get_event_logs_data

def calculate_health_scores() -> dict:
    """Run diagnostics queries and calculate category and overall health scores deterministically."""
    scores = {}
    
    # 1. CPU Score
    try:
        cpu = get_cpu_data()
        scores["CPU"] = max(0, 100 - int(cpu["cpu_percent"]))
    except Exception:
        scores["CPU"] = 100
        
    # 2. Memory Score
    try:
        mem = get_memory_data()
        scores["Memory"] = max(0, 100 - int(mem["ram_percent"]))
    except Exception:
        scores["Memory"] = 100
        
    # 3. Storage Score
    try:
        storage = get_storage_data()
        if storage["partitions"]:
            max_used = max(p["percent_used"] for p in storage["partitions"])
            scores["Storage"] = max(0, 100 - int(max_used))
        else:
            scores["Storage"] = 100
    except Exception:
        scores["Storage"] = 100
        
    # 4. Network Score
    try:
        net = get_network_data()
        net_score = 100
        if not net["gateway_reachable"]:
            net_score -= 40
        if not net["dns_resolvable"]:
            net_score -= 20
        if not net["internet_reachable"]:
            net_score -= 40
        if net["latency_ms"] > 150:
            net_score -= 10
        elif net["latency_ms"] > 300:
            net_score -= 20
        scores["Network"] = max(0, net_score)
    except Exception:
        scores["Network"] = 100
        
    # 5. Services Score
    try:
        services = get_services_data()
        if services["error"]:
            scores["Services"] = 100  # Fallback/Healthy on non-Windows
        else:
            stopped_count = len(services["stopped_auto_services"])
            scores["Services"] = max(50, 100 - (stopped_count * 10))
    except Exception:
        scores["Services"] = 100
        
    # 6. Startup Score
    try:
        startup = get_startup_data()
        if startup["error"]:
            scores["Startup"] = 100  # Fallback/Healthy on non-Windows
        else:
            deduction = 0
            for item in startup["startup_items"]:
                if item["impact"] == "HIGH":
                    deduction += 10
                elif item["impact"] == "MEDIUM":
                    deduction += 5
            scores["Startup"] = max(40, 100 - deduction)
    except Exception:
        scores["Startup"] = 100
        
    # 7. Reliability/Logs Score
    try:
        logs = get_event_logs_data(days=1)
        if logs["error"]:
            scores["Reliability"] = 100  # Fallback on non-Windows
        else:
            deduction = (logs["critical_count"] * 15) + (logs["error_count"] * 5)
            scores["Reliability"] = max(30, 100 - deduction)
    except Exception:
        scores["Reliability"] = 100

    # Calculate overall health score
    scores["OVERALL"] = int(sum(scores.values()) / len(scores))
    return scores
