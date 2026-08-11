import json
import urllib.request
from vanta.config import OLLAMA_BASE_URL, VANTA_MODEL
from vanta.agent.schemas import DiagnosticReport, Finding
from vanta.diagnostics.health import calculate_health_scores
from vanta.tools.system import get_system_info_data
from vanta.tools.cpu import get_cpu_data
from vanta.tools.memory import get_memory_data
from vanta.tools.storage import get_storage_data
from vanta.tools.network import get_network_data
from vanta.tools.services import get_services_data
from vanta.tools.startup import get_startup_data
from vanta.tools.logs import get_event_logs_data

def run_rule_based_diagnostics() -> DiagnosticReport:
    """Evaluate system metrics using local heuristic rules to generate findings."""
    findings = []
    
    # 1. CPU Rule
    try:
        cpu = get_cpu_data()
        if cpu["cpu_percent"] >= 90:
            findings.append(Finding(
                title="Extremely High CPU Usage",
                category="CPU",
                severity="CRITICAL",
                evidence=f"CPU utilization is at {cpu['cpu_percent']}%",
                possible_causes=["Resource-intensive processes running", "Malware or coin miners", "Stuck system tasks"],
                confidence="HIGH",
                recommendation="Identify high-CPU processes and terminate them. Close unnecessary background programs.",
                requires_action=False
            ))
        elif cpu["cpu_percent"] >= 70:
            findings.append(Finding(
                title="Moderate CPU Usage",
                category="CPU",
                severity="WARNING",
                evidence=f"CPU utilization is at {cpu['cpu_percent']}%",
                possible_causes=["Active application tasks", "Ongoing system index operations"],
                confidence="MEDIUM",
                recommendation="Monitor CPU consumers. Close heavy apps if the system feels sluggish.",
                requires_action=False
            ))
    except Exception:
        pass

    # 2. RAM Rule
    try:
        mem = get_memory_data()
        if mem["ram_percent"] >= 90:
            findings.append(Finding(
                title="Critical Memory Pressure",
                category="Memory",
                severity="CRITICAL",
                evidence=f"RAM utilization is at {mem['ram_percent']}% ({mem['ram_used_gb']} GB used)",
                possible_causes=["Too many active processes", "Memory leak in running software"],
                confidence="HIGH",
                recommendation="Close heavy memory-consuming programs (e.g. browser tabs, editors).",
                requires_action=False
            ))
        elif mem["ram_percent"] >= 75:
            findings.append(Finding(
                title="High Memory Usage",
                category="Memory",
                severity="ATTENTION",
                evidence=f"RAM utilization is at {mem['ram_percent']}%",
                possible_causes=["Multiple programs open", "Caching of system tasks"],
                confidence="HIGH",
                recommendation="Review open programs. Close apps you are not actively using.",
                requires_action=False
            ))
    except Exception:
        pass

    # 3. Disk Space Rule
    try:
        storage = get_storage_data()
        for p in storage["partitions"]:
            if p["status"] == "CRITICAL":
                findings.append(Finding(
                    title=f"Drive {p['mountpoint']} Low Space",
                    category="Storage",
                    severity="CRITICAL",
                    evidence=f"Drive has only {p['percent_free']}% free space left ({p['free_gb']} GB free)",
                    possible_causes=["Accumulated temp files", "Large downloaded files or programs"],
                    confidence="HIGH",
                    recommendation="Run Disk Cleanup, uninstall unused apps, or move large files to secondary storage.",
                    requires_action=True
                ))
            elif p["status"] == "WARNING":
                findings.append(Finding(
                    title=f"Drive {p['mountpoint']} Near Capacity",
                    category="Storage",
                    severity="WARNING",
                    evidence=f"Drive has {p['percent_free']}% free space left ({p['free_gb']} GB free)",
                    possible_causes=["Normal system growth", "Large logs or temporary cache"],
                    confidence="HIGH",
                    recommendation="Free up space by deleting temporary caches or system junk files.",
                    requires_action=True
                ))
    except Exception:
        pass

    # 4. Network Connection Rule
    try:
        net = get_network_data()
        if not net["gateway_reachable"]:
            findings.append(Finding(
                title="Default Gateway Unreachable",
                category="Network",
                severity="CRITICAL",
                evidence=f"Ping to gateway {net['gateway']} failed",
                possible_causes=["Network adapter disabled", "Ethernet disconnected", "Router/Modem powered off"],
                confidence="HIGH",
                recommendation="Check your physical network connection or toggle your network adapter.",
                requires_action=False
            ))
        elif not net["internet_reachable"]:
            findings.append(Finding(
                title="No Internet Connection",
                category="Network",
                severity="CRITICAL",
                evidence="DNS resolved google.com but ping to 8.8.8.8 failed",
                possible_causes=["ISP outage", "Router loss of internet access", "Firewall rules block ping"],
                confidence="HIGH",
                recommendation="Verify network WAN lights. Restart modem/router. Contact your ISP if unresolved.",
                requires_action=False
            ))
        elif not net["dns_resolvable"]:
            findings.append(Finding(
                title="DNS Name Resolution Failed",
                category="Network",
                severity="WARNING",
                evidence="Could not resolve host google.com",
                possible_causes=["DNS servers unresponsive", "Invalid DNS configuration"],
                confidence="HIGH",
                recommendation="Change network DNS settings to public DNS (e.g. 8.8.8.8 or 1.1.1.1).",
                requires_action=True
            ))
        elif net["latency_ms"] > 150:
            findings.append(Finding(
                title="High Network Latency",
                category="Network",
                severity="WARNING",
                evidence=f"Average external latency is {net['latency_ms']} ms",
                possible_causes=["Local network congestion", "Background downloads/updates", "Poor Wi-Fi signal"],
                confidence="MEDIUM",
                recommendation="Suspend active downloads. Move closer to the router if using Wi-Fi.",
                requires_action=False
            ))
    except Exception:
        pass

    # 5. Service Rules
    try:
        services = get_services_data()
        if not services["error"] and services["stopped_auto_services"]:
            stopped_services = services["stopped_auto_services"]
            findings.append(Finding(
                title=f"{len(stopped_services)} Stopped Auto Services",
                category="Services",
                severity="WARNING",
                evidence=f"Services like {', '.join(s['name'] for s in stopped_services[:3])} are auto-start but stopped",
                possible_causes=["Crashed service tasks", "Service disabled manually", "System startup delays"],
                confidence="HIGH",
                recommendation="Inspect service logs and restart failed automatic services.",
                requires_action=True
            ))
    except Exception:
        pass

    # 6. Startup Rule
    try:
        startup = get_startup_data()
        if not startup["error"] and startup["startup_items"]:
            items = startup["startup_items"]
            high_impact_count = sum(1 for item in items if item["impact"] == "HIGH")
            if high_impact_count >= 3:
                findings.append(Finding(
                    title="High Startup Load",
                    category="Startup",
                    severity="WARNING",
                    evidence=f"{high_impact_count} high-impact apps configured to launch at boot",
                    possible_causes=["Third-party apps adding themselves to startup automatically"],
                    confidence="HIGH",
                    recommendation="Disable unnecessary high-impact apps from starting up via Task Manager or /action.",
                    requires_action=True
                ))
    except Exception:
        pass

    # 7. Event Log Rule
    try:
        logs = get_event_logs_data(days=1)
        if not logs["error"]:
            total_issues = logs["critical_count"] + logs["error_count"]
            if total_issues >= 10:
                findings.append(Finding(
                    title="High Rate of System Errors",
                    category="Logs",
                    severity="ATTENTION",
                    evidence=f"Found {logs['critical_count']} critical and {logs['error_count']} error events in last 24h",
                    possible_causes=["Driver conflicts", "Failing hardware (e.g. disk bad sectors)", "Unresolved service crashes"],
                    confidence="MEDIUM",
                    recommendation="Run event log diagnostics or check reliability monitor details.",
                    requires_action=False
                ))
    except Exception:
        pass

    scores = calculate_health_scores()
    
    # Simple summary if no findings
    summary = "All monitored parameters are within safe ranges." if not findings else f"Found {len(findings)} issues during diagnostic checks."
    
    return DiagnosticReport(
        findings=findings,
        overall_health_score=scores["OVERALL"],
        categories_scores={k: v for k, v in scores.items() if k != "OVERALL"},
        summary=summary
    )

def is_ollama_online() -> bool:
    """Ping the Ollama tags endpoint to check server availability."""
    try:
        # Check connection
        with urllib.request.urlopen(f"{OLLAMA_BASE_URL}/api/tags", timeout=2) as response:
            return response.status == 200
    except Exception:
        return False

def run_diagnostics_scan() -> DiagnosticReport:
    """Run full diagnostic checks. Fallback to rule-based analysis if Ollama is unavailable."""
    report = run_rule_based_diagnostics()
    
    if not is_ollama_online():
        # Fallback to local rule-based diagnostics
        return report
        
    # Ollama is online, enrich using LLM
    try:
        # Construct summary prompt for Ollama to write structured findings or write natural summaries
        import langchain_ollama
        from langchain_core.messages import HumanMessage
        
        # We query Ollama model directly using langchain to refine the summary and findings
        llm = langchain_ollama.ChatOllama(
            model=VANTA_MODEL,
            base_url=OLLAMA_BASE_URL,
            temperature=0,
            format="json"
        )
        
        system_summary_prompt = (
            f"You are the diagnostic engine of VANTA (Virtual Autonomous Network & Technical Analyst).\n"
            f"Given the following system statistics, local rule-based findings, and calculated health scores, "
            f"generate an improved DiagnosticReport JSON. Maintain the rules and scores, but write a highly professional, "
            f"cohesive natural language 'summary' and polish the 'findings' titles/descriptions. Do not invent new measurements.\n\n"
            f"Format response strictly as JSON that parses directly into this schema:\n"
            f"{{\n"
            f"  \"findings\": [\n"
            f"    {{\"title\": \"string\", \"category\": \"string\", \"severity\": \"string\", \"evidence\": \"string\", \"possible_causes\": [\"string\"], \"confidence\": \"string\", \"recommendation\": \"string\", \"requires_action\": true/false}}\n"
            f"  ],\n"
            f"  \"overall_health_score\": {report.overall_health_score},\n"
            f"  \"categories_scores\": {json.dumps(report.categories_scores)},\n"
            f"  \"summary\": \"A short overall description.\"\n"
            f"}}\n\n"
            f"Input Data:\n"
            f"Heuristic findings count: {len(report.findings)}\n"
            f"Findings raw list: {json.dumps([f.model_dump() for f in report.findings])}\n"
        )
        
        msg = HumanMessage(content=system_summary_prompt)
        res = llm.invoke([msg])
        
        res_json = json.loads(res.content)
        # Parse it back to Pydantic
        parsed_findings = []
        for f in res_json.get("findings", []):
            parsed_findings.append(Finding(**f))
            
        return DiagnosticReport(
            findings=parsed_findings,
            overall_health_score=res_json.get("overall_health_score", report.overall_health_score),
            categories_scores=res_json.get("categories_scores", report.categories_scores),
            summary=res_json.get("summary", report.summary)
        )
    except Exception:
        # Fallback to local report if model errors
        return report
