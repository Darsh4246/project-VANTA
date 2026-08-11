from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.console import Group
from vanta.ui.theme import get_theme

def render_report_panel(report_data: dict) -> Panel:
    """Renders the main diagnostic report card panel."""
    theme = get_theme()
    score = report_data.get("overall_health_score", 100)
    findings = report_data.get("findings", [])
    
    # Severity counters
    critical_count = sum(1 for f in findings if f.get("severity") == "CRITICAL")
    attention_count = sum(1 for f in findings if f.get("severity") == "ATTENTION")
    warning_count = sum(1 for f in findings if f.get("severity") == "WARNING")
    info_count = sum(1 for f in findings if f.get("severity") == "INFO")
    
    # Determine overall health color
    if score >= 90:
        score_color = theme["success"]
    elif score >= 70:
        score_color = theme["secondary"]
    elif score >= 50:
        score_color = theme["highlight"]
    else:
        score_color = theme["accent"]
        
    score_text = Text(f"Overall Health: {score}/100", style=f"bold {score_color}")
    
    counts_lines = [
        Text(""),
        Text(f" 🔴 Critical:     {critical_count}", style="bold red" if critical_count > 0 else "dim white"),
        Text(f" 🟠 Attention:    {attention_count}", style=f"bold {theme['secondary']}" if attention_count > 0 else "dim white"),
        Text(f" ⚠ Warning:      {warning_count}", style=f"bold {theme['highlight']}" if warning_count > 0 else "dim white"),
        Text(f" ℹ Information:  {info_count}", style="bold cyan" if info_count > 0 else "dim white"),
        Text("")
    ]
    
    top_issue = "None"
    if findings:
        # Sort findings by severity (CRITICAL > ATTENTION > WARNING > INFO)
        sev_rank = {"CRITICAL": 0, "ATTENTION": 1, "WARNING": 2, "INFO": 3}
        sorted_findings = sorted(findings, key=lambda f: sev_rank.get(f.get("severity", "INFO"), 4))
        top_issue = sorted_findings[0].get("title", "Unknown issue")
        
    counts_lines.append(Text(f"Top Issue: {top_issue}", style=f"bold {theme['primary']}" if findings else "dim white"))
    
    return Panel(
        Group(*counts_lines),
        title=f"[bold {theme['primary']}] VANTA SYSTEM DIAGNOSTIC REPORT [/bold {theme['primary']}]",
        title_align="left",
        border_style=theme["secondary"],
        padding=(1, 2)
    )

def render_findings_table(findings: list) -> Table:
    """Creates a beautiful rich Table of diagnostic findings."""
    theme = get_theme()
    table = Table(
        border_style=theme["secondary"],
        header_style=f"bold {theme['primary']}",
        show_header=True,
        expand=True
    )
    
    table.add_column("Severity", width=12, style="bold")
    table.add_column("Category", width=12)
    table.add_column("Diagnostic Finding", style="white")
    table.add_column("Confidence", width=10)
    table.add_column("Recommendation", style="dim white")
    
    sev_colors = {
        "CRITICAL": "bold red",
        "ATTENTION": f"bold {theme['secondary']}",
        "WARNING": f"bold {theme['highlight']}",
        "INFO": "bold cyan",
        "HEALTHY": f"bold {theme['success']}"
    }
    
    for f in findings:
        sev = f.get("severity", "INFO").upper()
        sev_color = sev_colors.get(sev, "white")
        
        table.add_row(
            Text(sev, style=sev_color),
            f.get("category", "General"),
            f.get("title", "No Title"),
            f.get("confidence", "HIGH"),
            f.get("recommendation", "N/A")
        )
        
    return table

def render_health_breakdown(health_data: dict) -> Panel:
    """Renders system metrics health score card breakdown."""
    theme = get_theme()
    
    table = Table.grid(padding=(0, 2))
    table.add_column("Category", style=f"bold {theme['primary']}", width=15)
    table.add_column("Score", style="bold white", width=10)
    table.add_column("Status", width=15)
    
    overall = health_data.get("OVERALL", 100)
    
    # We display each subsystem score
    for category, score in health_data.items():
        if category == "OVERALL":
            continue
        
        if score >= 90:
            status = f"[bold {theme['success']}]HEALTHY[/bold {theme['success']}]"
        elif score >= 70:
            status = f"[bold {theme['highlight']}]STABLE[/bold {theme['highlight']}]"
        elif score >= 50:
            status = f"[bold {theme['secondary']}]WARNING[/bold {theme['secondary']}]"
        else:
            status = "[bold red]CRITICAL[/bold red]"
            
        table.add_row(category.title(), f"{score}/100", status)
        
    # Render overall line divider
    divider = Text("─" * 40, style="dim white")
    
    if overall >= 90:
        overall_status = f"[bold {theme['success']}]HEALTHY[/bold {theme['success']}]"
    elif overall >= 70:
        overall_status = f"[bold {theme['highlight']}]STABLE[/bold {theme['highlight']}]"
    else:
        overall_status = f"[bold {theme['secondary']}]ATTENTION[/bold {theme['secondary']}]"
        
    overall_row = Table.grid(padding=(0, 2))
    overall_row.add_column("Category", style=f"bold {theme['secondary']}", width=15)
    overall_row.add_column("Score", style=f"bold {theme['primary']}", width=10)
    overall_row.add_column("Status", width=15)
    overall_row.add_row("OVERALL", f"{overall}/100", overall_status)
    
    return Panel(
        Group(table, divider, overall_row),
        title=f"[bold {theme['primary']}] VANTA SYSTEM HEALTH BREAKDOWN [/bold {theme['primary']}]",
        border_style=theme["secondary"],
        padding=(1, 2)
    )

def render_confirmation_panel(action_name: str, risk: str, reason: str) -> Panel:
    """Renders the approval window for executing a system-modifying repair action."""
    theme = get_theme()
    
    risk_color = "bold red" if risk.upper() == "HIGH" else (f"bold {theme['secondary']}" if risk.upper() == "MEDIUM" else f"bold {theme['success']}")
    
    group = Group(
        Text(""),
        Text(f"Action: {action_name}", style=f"bold {theme['highlight']}"),
        Text(f"Risk:   {risk.upper()}", style=risk_color),
        Text(""),
        Text("Reason:", style="bold white"),
        Text(reason, style="dim white"),
        Text(""),
        Text("Proceed? [y/N] > ", style=f"bold {theme['primary']}")
    )
    
    return Panel(
        group,
        title="[bold red] ACTION REQUIRES APPROVAL [/bold red]",
        border_style="red",
        padding=(0, 2)
    )
