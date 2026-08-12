import os
import sys
import time
import json
import sqlite3
from datetime import datetime
from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.markdown import Markdown
from rich.align import Align
from rich.spinner import Spinner as RichSpinner
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage

# Configuration & DB imports
from vanta.config import VANTA_MODEL, OLLAMA_BASE_URL, VANTA_SAFE_MODE, DB_PATH
from vanta.database.history import log_session, get_history, get_last_scan_report
from vanta.ui.theme import get_theme, load_active_theme, save_active_theme, THEMES, get_theme_key
from vanta.ui.animations import run_startup_animation
from vanta.ui.panels import (
    render_report_panel,
    render_findings_table,
    render_health_breakdown,
    render_confirmation_panel
)
from vanta.ui.terminal import get_input, console

# Diagnostics & Agent imports
from vanta.diagnostics.engine import run_diagnostics_scan, run_rule_based_diagnostics, is_ollama_online
from vanta.agent.agent import build_vanta_agent, set_confirm_callback, ALL_TOOLS
from vanta.agent.memory import ConversationMemory
from vanta.agent.prompts import SYSTEM_PROMPT

# Import tools for CLI execution
from vanta.tools.cpu import cpu_diagnostics
from vanta.tools.memory import memory_diagnostics
from vanta.tools.processes import process_diagnostics
from vanta.tools.storage import storage_diagnostics
from vanta.tools.hardware import hardware_diagnostics
from vanta.tools.network import network_diagnostics
from vanta.tools.services import service_diagnostics
from vanta.tools.startup import startup_diagnostics
from vanta.tools.software import software_diagnostics
from vanta.tools.logs import log_diagnostics
from vanta.tools.devices import device_driver_diagnostics

def confirm_callback(action_name: str, risk: str, reason: str) -> bool:
    """CLI confirmation prompt for modifying actions."""
    panel = render_confirmation_panel(action_name, risk, reason)
    console.print(panel)
    try:
        ans = sys.stdin.readline().strip().lower()
        return ans in ("y", "yes")
    except Exception:
        return False

# Bind the confirmation callback to the agent action handlers
set_confirm_callback(confirm_callback)

def render_execution_status(steps: list, is_running: bool = True) -> Panel:
    """Render a beautiful live panel detailing current tool executions."""
    theme = get_theme()
    group_elements = []
    
    if steps:
        table = Table.grid(padding=(0, 1))
        table.add_column("Status", width=4)
        table.add_column("Step Description")
        
        for step in steps:
            name = step['name']
            args = step['args']
            status = step['status']
            
            args_str = ", ".join(f"{k}={repr(v)}" for k, v in args.items())
            if len(args_str) > 60:
                args_str = args_str[:57] + "..."
                
            if status == 'running':
                icon = f"[bold {theme['highlight']}]*[/bold {theme['highlight']}]"
                desc = f"Running: [bold {theme['primary']}]{name}[/bold {theme['primary']}]({args_str})..."
            else:
                icon = f"[bold {theme['success']}]+[/bold {theme['success']}]"
                desc = f"Finished: [bold {theme['primary']}]{name}[/bold {theme['primary']}]({args_str})"
            table.add_row(icon, desc)
            
            if status == 'completed' and step.get('result'):
                res = str(step['result']).strip()
                if res:
                    res_lines = res.split('\n')
                    res_snippet = res_lines[0]
                    if len(res_snippet) > 85:
                        res_snippet = res_snippet[:82] + "..."
                    if len(res_lines) > 1:
                        res_snippet += f" (+ {len(res_lines) - 1} more lines)"
                    table.add_row("", f"  [dim white]Result: {res_snippet}[/dim white]")
                    
        group_elements.append(table)
        group_elements.append("") 
        
    if is_running:
        spinner_grid = Table.grid(padding=(0, 2))
        spinner_grid.add_row(RichSpinner(theme['spinner_type'], style=theme['secondary']), Text("VANTA is diagnosing...", style="bold white"))
        group_elements.append(spinner_grid)
        
    return Panel(
        Group(*[el for el in group_elements if el != ""]),
        title=f"[bold {theme['primary']}] VANTA AGENT ACTIVITY TRACE [/bold {theme['primary']}]",
        border_style=theme['secondary'],
        padding=(1, 2)
    )

def print_help():
    """Display commands and prompt helper."""
    theme = get_theme()
    help_text = f"""[bold {theme['primary']}]CLI Diagnostic Commands:[/bold {theme['primary']}]
  [bold {theme['secondary']}]help[/bold {theme['secondary']}]          Display this command overview
  [bold {theme['secondary']}]status[/bold {theme['secondary']}]        Show agent configurations and environment state
  [bold {theme['secondary']}]scan[/bold {theme['secondary']}]          Execute a comprehensive system scan
  [bold {theme['secondary']}]hardware[/bold {theme['secondary']}]      Display hardware info (motherboard, GPU, sensors)
  [bold {theme['secondary']}]devices[/bold {theme['secondary']}]       List system hardware devices and driver states
  [bold {theme['secondary']}]cpu[/bold {theme['secondary']}]           Print detailed CPU statistics
  [bold {theme['secondary']}]memory[/bold {theme['secondary']}]        Print RAM and pagefile metrics
  [bold {theme['secondary']}]processes[/bold {theme['secondary']}]     Show high-usage processes
  [bold {theme['secondary']}]storage[/bold {theme['secondary']}]       Inspect disk partitions and capacities
  [bold {theme['secondary']}]network[/bold {theme['secondary']}]       Test ping, gateway, and DNS configuration
  [bold {theme['secondary']}]services[/bold {theme['secondary']}]      Check stopped auto-run Windows services
  [bold {theme['secondary']}]startup[/bold {theme['secondary']}]       Display startup applications and boot impact
  [bold {theme['secondary']}]software[/bold {theme['secondary']}]      Inventory installed programs in the registry
  [bold {theme['secondary']}]logs[/bold {theme['secondary']}]          Summarize critical events from event logs
  [bold {theme['secondary']}]history[/bold {theme['secondary']}]       Show history of past diagnostics
  [bold {theme['secondary']}]safe-mode[/bold {theme['secondary']}]     View or toggle Safe Mode setting
  [bold {theme['secondary']}]settings[/bold {theme['secondary']}]      Select a console color theme
  [bold {theme['secondary']}]about[/bold {theme['secondary']}]         View product details and design credits
  [bold {theme['secondary']}]clear[/bold {theme['secondary']}]         Flush conversation memory context
  [bold {theme['secondary']}]exit[/bold {theme['secondary']}]          Safely close the terminal console

[bold {theme['primary']}]Natural Language Diagnostics Examples:[/bold {theme['primary']}]
  - "Why is my computer running so slow?"
  - "Check if my DNS server is working properly."
  - "What applications are taking up all my RAM?"
  - "Clean up temporary files on my hard drive."
"""
    console.print(
        Panel(
            help_text.strip(),
            title=f"[bold {theme['primary']}] VANTA CLI HELP SYSTEM [/bold {theme['primary']}]",
            border_style=theme['secondary'],
            padding=(1, 2)
        )
    )

def print_settings_menu():
    """Render settings theme modification console card."""
    theme = get_theme()
    current_key = get_theme_key()
    
    table = Table(
        title=f"[bold {theme['primary']}]Select Color Theme[/bold {theme['primary']}]",
        border_style=theme['secondary'],
        header_style=f"bold {theme['primary']}",
        show_header=True
    )
    table.add_column("Command", style="cyan", width=25)
    table.add_column("Theme Name", width=20)
    table.add_column("Description", style="white")
    table.add_column("Preview", width=15)
    
    for key, t in THEMES.items():
        marker = " [bold green]*[/bold green]" if key == current_key else ""
        theme_styled = f"[bold {t['primary']}]{t['name']}[/bold {t['primary']}]"
        cmd = f"settings {key.replace('_', ' ')}"
        preview = f"[bold {t['primary']}]█[/bold {t['primary']}][bold {t['secondary']}]█[/bold {t['secondary']}][bold {t['highlight']}]█[/bold {t['highlight']}][bold {t['accent']}]█[/bold {t['accent']}]"
        table.add_row(cmd, theme_styled + marker, t["desc"], preview)
        
    console.print(table)
    console.print(Align.center(Text("Toggle theme using: settings <theme name> (e.g. settings solar flare)", style="dim")))

def print_status_panel():
    """Display environment configurations and model endpoints status."""
    theme = get_theme()
    online = is_ollama_online()
    status_text = f"[bold {theme['success']}]Online[/bold {theme['success']}]" if online else "[bold red]Offline (Rule-Based Heuristics Fallback)[/bold red]"
    
    table = Table.grid(padding=(0, 2))
    table.add_column("Setting", style=f"bold {theme['primary']}", width=20)
    table.add_column("Value", style="white")
    
    table.add_row("MODEL", VANTA_MODEL)
    table.add_row("OLLAMA HOST", OLLAMA_BASE_URL)
    table.add_row("AI ENGINE STATUS", status_text)
    table.add_row("SAFE MODE", "ENABLED (Read-Only)" if VANTA_SAFE_MODE else "DISABLED (Modifications Allowed)")
    table.add_row("DATABASE PATH", str(DB_PATH))
    
    console.print(
        Panel(
            table,
            title=f"[bold {theme['primary']}] VANTA DIAGNOSTICS STATUS [/bold {theme['primary']}]",
            border_style=theme['secondary'],
            padding=(1, 2)
        )
    )

def handle_natural_language_offline(query: str):
    """Run local heuristic rules if the user asks a question and Ollama is offline."""
    theme = get_theme()
    console.print(f"[bold {theme['highlight']}]⚠ Ollama is offline. Executing heuristic system analysis...[/bold {theme['highlight']}]\n")
    
    # Run heuristics
    report = run_rule_based_diagnostics()
    
    # Match keywords to filter findings
    query_lower = query.lower()
    matched_findings = []
    
    for f in report.findings:
        if f.category.lower() in query_lower or f.title.lower() in query_lower:
            matched_findings.append(f)
            
    # If no specific category matched, print all findings
    findings_to_show = matched_findings if matched_findings else report.findings
    
    if findings_to_show:
        console.print(render_findings_table(findings_to_show))
    else:
        console.print(f"[bold {theme['success']}]✓ No heuristic issues detected corresponding to '{query}'.[/bold {theme['success']}]")
        
    console.print(f"\n[dim white]System overall health score: {report.overall_health_score}/100[/dim white]")

def main():
    load_active_theme()
    run_startup_animation(console)
    
    # Check Ollama connection status
    theme = get_theme()
    online = is_ollama_online()
    if not online:
        console.print(
            Panel(
                f"[bold red]AI Engine Offline.[/bold red]\n\n"
                f"Ollama could not be reached at [yellow]{OLLAMA_BASE_URL}[/yellow].\n"
                f"VANTA will run in [bold {theme['highlight']}]Offline Local Heuristic Mode[/bold {theme['highlight']}].\n"
                f"You can still run diagnostic commands directly.",
                title="AI Engine Status",
                border_style="red"
            )
        )
    else:
        console.print(
            Panel(
                f"[bold {theme['success']}]AI Engine Online.[/bold {theme['success']}]\n"
                f"Agent using model: [bold {theme['primary']}]{VANTA_MODEL}[/bold {theme['primary']}].\n"
                f"Safe Mode is [bold {theme['highlight']}]{'Enabled' if VANTA_SAFE_MODE else 'Disabled'}[/bold {theme['highlight']}].",
                title="AI Engine Status",
                border_style=theme['secondary']
            )
        )
        
    memory = ConversationMemory()
    
    # Compile tools list for quick access by name
    tools_map = {t.name: t for t in ALL_TOOLS}
    
    while True:
        user_input = get_input("VANTA")
        if not user_input:
            continue
            
        command = user_input.strip().lower()
        if command in ("exit", "quit", "/exit", "/quit"):
            console.print(f"\n[bold {theme['primary']}]Goodbye. System analysis suspended.[/bold {theme['primary']}]")
            break
            
        # Match standard CLI commands
        if command in ("help", "/help"):
            print_help()
            continue
            
        if command in ("status", "/status"):
            print_status_panel()
            continue
            
        if command in ("about", "/about"):
            console.print(Panel(
                f"VANTA — Virtual Autonomous Network & Technical Analyst\n"
                f"Version 1.0.0 (Production Build)\n\n"
                f"Designed as a natural language technician and monitoring agent.\n"
                f"Built using LangChain, Ollama, and Rich terminal UI.\n"
                f"Default Theme: {theme['name']}",
                title="About VANTA",
                border_style=theme['secondary']
            ))
            continue
            
        if command in ("clear", "/clear"):
            memory.clear()
            console.print(f"[bold {theme['success']}]Conversation history cleared.[/bold {theme['success']}]")
            continue
            
        if command in ("safe-mode", "/safe-mode"):
            console.print(f"Safe Mode status: [bold {theme['primary']}]{'ENABLED (Read-only diagnostics)' if VANTA_SAFE_MODE else 'DISABLED (System modifying active)'}[/bold {theme['primary']}]")
            continue
            
        if command in ("scan", "/scan"):
            with console.status(f"[bold {theme['secondary']}]Running full diagnostic scan...[/bold {theme['secondary']}]", spinner=theme['spinner_type']):
                report = run_diagnostics_scan()
            console.print(render_report_panel(report.model_dump()))
            if report.findings:
                console.print(render_findings_table(report.model_dump()["findings"]))
            else:
                console.print(f"[bold {theme['success']}]✓ No system diagnostic issues found![/bold {theme['success']}]")
            # Log scan history
            log_session(
                request="System full diagnostics scan",
                tools_used=["system_info", "cpu_diagnostics", "memory_diagnostics", "storage_diagnostics", "network_diagnostics", "service_diagnostics", "startup_diagnostics", "log_diagnostics"],
                findings=[f.model_dump() for f in report.findings],
                recommendations=report.summary,
                action_approved=False,
                action_completed=False,
                verification="Scan complete"
            )
            continue
            
        if command in ("cpu", "/cpu"):
            console.print(Panel(cpu_diagnostics.invoke({}), title="CPU Diagnostics", border_style=theme['secondary']))
            continue
            
        if command in ("memory", "/memory"):
            console.print(Panel(memory_diagnostics.invoke({}), title="Memory Diagnostics", border_style=theme['secondary']))
            continue
            
        if command in ("processes", "/processes"):
            console.print(Panel(process_diagnostics.invoke({}), title="Process Monitor", border_style=theme['secondary']))
            continue
            
        if command in ("storage", "/storage"):
            console.print(Panel(storage_diagnostics.invoke({}), title="Storage diagnostics", border_style=theme['secondary']))
            continue
            
        if command in ("network", "/network"):
            console.print(Panel(network_diagnostics.invoke({}), title="Network diagnostics", border_style=theme['secondary']))
            continue
            
        if command in ("services", "/services"):
            console.print(Panel(service_diagnostics.invoke({}), title="Windows Services", border_style=theme['secondary']))
            continue
            
        if command in ("startup", "/startup"):
            console.print(Panel(startup_diagnostics.invoke({}), title="Startup Diagnostics", border_style=theme['secondary']))
            continue
            
        if command in ("software", "/software"):
            console.print(Panel(software_diagnostics.invoke({}), title="Software Inventory", border_style=theme['secondary']))
            continue
            
        if command in ("logs", "/logs"):
            console.print(Panel(log_diagnostics.invoke({}), title="Windows Event Logs", border_style=theme['secondary']))
            continue
            
        if command in ("hardware", "/hardware"):
            console.print(Panel(hardware_diagnostics.invoke({}), title="Hardware Diagnostics", border_style=theme['secondary']))
            continue
            
        if command == "devices" or command.startswith("devices ") or command in ("/devices", "/devices "):
            parts = user_input.split(maxsplit=1)
            if len(parts) == 1:
                res = device_driver_diagnostics.invoke({})
            else:
                arg = parts[1].strip()
                if arg.lower() in ("problematic", "error", "degraded"):
                    res = device_driver_diagnostics.invoke({"show_problematic_only": True})
                elif arg.lower() in ("biometric", "usb", "net", "display", "system", "bluetooth", "media", "keyboard", "mouse"):
                    res = device_driver_diagnostics.invoke({"filter_class": arg})
                else:
                    res = device_driver_diagnostics.invoke({"query": arg})
            console.print(Panel(res, title="Device & Driver Diagnostics", border_style=theme['secondary']))
            continue
            
        if command in ("history", "/history"):
            hist = get_history()
            if not hist:
                console.print("[dim white]No history entries logged yet.[/dim white]")
                continue
            table = Table(title="Diagnostic Session History", border_style=theme['secondary'], header_style=f"bold {theme['primary']}")
            table.add_column("ID", width=4)
            table.add_column("Timestamp")
            table.add_column("Query/Request")
            table.add_column("Recommendations Summary")
            for r in hist:
                table.add_row(str(r["id"]), r["timestamp"], r["request"], r["recommendations"][:60] + "...")
            console.print(table)
            continue
            
        if command == "settings" or command.startswith("settings "):
            parts = user_input.split(maxsplit=1)
            if len(parts) == 1:
                print_settings_menu()
            else:
                target_theme = parts[1].strip().lower().replace(" ", "_")
                if target_theme in THEMES:
                    save_active_theme(target_theme)
                    theme = get_theme()
                    console.print(f"\n[bold {theme['success']}]Theme changed to: {theme['name']}![/bold {theme['success']}]")
                else:
                    console.print(f"[bold red]Unknown theme '{parts[1]}'.[/bold red] Type 'settings' to view themes.")
            continue
            
        # If it is natural language
        online = is_ollama_online()
        if not online:
            # Fallback natural language
            handle_natural_language_offline(user_input)
            continue
            
        # Agent execution loop (Online Mode)
        memory.add_user_message(user_input)
        
        # Build prompt message chain
        safe_mode_status = "ENABLED" if VANTA_SAFE_MODE else "DISABLED"
        agent_status_prompt = (
            f"\n\nCURRENT VANTA AGENT CONFIGURATION:\n"
            f"- Agent Safe Mode Setting: {safe_mode_status} (This is a safety configuration of the VANTA agent application restricting repairs to read-only diagnostics. It does NOT mean the Windows operating system is booted into Safe Mode.)"
        )
        messages = [SystemMessage(content=SYSTEM_PROMPT + agent_status_prompt)]
        for m in memory.get_messages():
            if m["role"] == "user":
                messages.append(HumanMessage(content=m["content"]))
            else:
                messages.append(AIMessage(content=m["content"]))
                
        steps = []
        final_answer = ""
        tools_used = []
        action_approved = False
        action_completed = False
        verification = "Diagnostics completed"
        
        try:
            agent = build_vanta_agent()
            
            with Live(render_execution_status(steps, is_running=True), console=console, refresh_per_second=6, transient=False) as live:
                while True:
                    live.update(render_execution_status(steps, is_running=True))
                    # Invoke model
                    response = agent.invoke(messages)
                    
                    if response.tool_calls:
                        # Append AIMessage describing tool calls to feed back to Ollama later
                        messages.append(AIMessage(content="", tool_calls=response.tool_calls))
                        
                        for tc in response.tool_calls:
                            tc_id = tc["id"]
                            tc_name = tc["name"]
                            tc_args = tc["args"]
                            
                            step_info = {
                                "type": "tool_call",
                                "id": tc_id,
                                "name": tc_name,
                                "args": tc_args,
                                "status": "running",
                                "result": None
                            }
                            steps.append(step_info)
                            live.update(render_execution_status(steps, is_running=True))
                            
                            tools_used.append(tc_name)
                            
                            # Intercept modifying actions for history log tracking
                            if "tool" in tc_name:
                                action_approved = True
                                
                            # Execute tool
                            tool_func = tools_map.get(tc_name)
                            if tool_func:
                                try:
                                    # Temporarily pause live view if we prompt confirmation
                                    if "tool" in tc_name:
                                        live.stop()
                                        
                                    result = tool_func.invoke(tc_args)
                                    
                                    if "tool" in tc_name:
                                        live.start()
                                        if "Successfully" in str(result):
                                            action_completed = True
                                            verification = str(result)
                                except Exception as e:
                                    result = f"Error: {e}"
                                    if "tool" in tc_name:
                                        live.start()
                            else:
                                result = f"Error: Tool {tc_name} not found."
                                
                            step_info["status"] = "completed"
                            step_info["result"] = result
                            live.update(render_execution_status(steps, is_running=True))
                            
                            # Append result message
                            messages.append(ToolMessage(content=str(result), tool_call_id=tc_id))
                    else:
                        final_answer = response.content
                        break
                        
                # Mark steps completed when loop ends
                for s in steps:
                    s["status"] = "completed"
                live.update(render_execution_status(steps, is_running=False))
                
        except Exception as e:
            final_answer = f"Agent error during execution: {e}"
            console.print(Panel(final_answer, border_style="red", title="Error"))
            
        if final_answer:
            console.print()
            console.print(
                Panel(
                    Markdown(final_answer),
                    title=f"[bold {theme['primary']}] VANTA RESPONSE [/bold {theme['primary']}]",
                    border_style=theme['secondary'],
                    padding=(1, 2)
                )
            )
            memory.add_assistant_message(final_answer)
            
            # Log execution history session
            log_session(
                request=user_input,
                tools_used=tools_used,
                findings=[],
                recommendations=final_answer,
                action_approved=action_approved,
                action_completed=action_completed,
                verification=verification
            )

if __name__ == "__main__":
    main()
