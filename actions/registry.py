from vanta.actions.executor import (
    restart_service_impl,
    clear_temp_files_impl,
    disable_startup_app_impl,
    flush_dns_impl
)

ACTION_REGISTRY = {
    "restart_service": {
        "name": "Restart Service",
        "description": "Restart a stopped or failed Windows service.",
        "risk": "MEDIUM",
        "handler": restart_service_impl
    },
    "clear_temp_files": {
        "name": "Clear Temporary Files",
        "description": "Clean files from user and system temp folders to free space.",
        "risk": "LOW",
        "handler": clear_temp_files_impl
    },
    "disable_startup_app": {
        "name": "Disable Startup App",
        "description": "Remove an app from starting up automatically with Windows.",
        "risk": "MEDIUM",
        "handler": disable_startup_app_impl
    },
    "flush_dns": {
        "name": "Flush DNS Cache",
        "description": "Clear the local DNS resolution cache.",
        "risk": "LOW",
        "handler": flush_dns_impl
    }
}

def execute_action(action_key: str, *args) -> str:
    """Execute action from registry after verifying registration."""
    action = ACTION_REGISTRY.get(action_key)
    if not action:
        return f"Error: Action '{action_key}' is not registered in the VANTA safety validation registry."
    
    try:
        res = action["handler"](*args)
        return res
    except Exception as e:
        return f"Action execution error: {e}"
