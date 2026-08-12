import os
import sys
from langchain_ollama import ChatOllama
from langchain.tools import tool

from vanta.config import VANTA_MODEL, OLLAMA_BASE_URL, VANTA_SAFE_MODE
from vanta.agent.prompts import SYSTEM_PROMPT

# Import tools
from vanta.tools.system import system_info
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

# Import action executors
from vanta.actions.registry import execute_action, ACTION_REGISTRY

# Define confirmation callback hook
_confirm_callback = None

def set_confirm_callback(callback):
    global _confirm_callback
    _confirm_callback = callback

# Define repair tools with safety validators
@tool
def restart_service_tool(service_name: str) -> str:
    """Request to restart a stopped or failed Windows service. Requires admin rights and user confirmation."""
    if VANTA_SAFE_MODE:
        return "Action Prohibited: Service modifications are disabled in Safe Mode."
        
    reason = f"Request to restart Windows service '{service_name}'."
    if _confirm_callback:
        approved = _confirm_callback("Restart Service", "MEDIUM", reason)
        if not approved:
            return "Action aborted by user permission rejection."
            
    return execute_action("restart_service", service_name)

@tool
def clear_temp_files_tool() -> str:
    """Request to delete temporary cache and log files to free storage space. Requires user confirmation."""
    if VANTA_SAFE_MODE:
        return "Action Prohibited: File deletions are disabled in Safe Mode."
        
    reason = "Request to delete temporary caches and log files from system temp directories."
    if _confirm_callback:
        approved = _confirm_callback("Clear Temporary Files", "LOW", reason)
        if not approved:
            return "Action aborted by user permission rejection."
            
    return execute_action("clear_temp_files")

@tool
def disable_startup_app_tool(app_name: str) -> str:
    """Request to disable an application from starting automatically on boot. Requires user confirmation."""
    if VANTA_SAFE_MODE:
        return "Action Prohibited: Registry modifications are disabled in Safe Mode."
        
    reason = f"Request to remove '{app_name}' from the user startup configuration."
    if _confirm_callback:
        approved = _confirm_callback("Disable Startup Application", "MEDIUM", reason)
        if not approved:
            return "Action aborted by user permission rejection."
            
    return execute_action("disable_startup_app", app_name)

@tool
def flush_dns_tool() -> str:
    """Request to flush local DNS cache. Requires user confirmation."""
    if VANTA_SAFE_MODE:
        return "Action Prohibited: Network configuration changes are disabled in Safe Mode."
        
    reason = "Request to flush DNS resolver cache."
    if _confirm_callback:
        approved = _confirm_callback("Flush DNS Cache", "LOW", reason)
        if not approved:
            return "Action aborted by user permission rejection."
            
    return execute_action("flush_dns")

# Compile tools list
ALL_TOOLS = [
    system_info,
    cpu_diagnostics,
    memory_diagnostics,
    process_diagnostics,
    storage_diagnostics,
    hardware_diagnostics,
    network_diagnostics,
    service_diagnostics,
    startup_diagnostics,
    software_diagnostics,
    log_diagnostics,
    device_driver_diagnostics,
    restart_service_tool,
    clear_temp_files_tool,
    disable_startup_app_tool,
    flush_dns_tool
]

def build_vanta_agent():
    """Build and compile the LangChain chat agent using Ollama."""
    llm = ChatOllama(
        model=VANTA_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=0.1,
        num_ctx=8192
    )
    
    # We bind tools
    llm_with_tools = llm.bind_tools(ALL_TOOLS)
    
    return llm_with_tools
