import os
import sys

def is_admin() -> bool:
    """Return True if the script is running with administrative privileges, False otherwise."""
    if sys.platform == "win32":
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            # Fallback check
            import subprocess
            res = subprocess.run("net session", capture_output=True, shell=True)
            return res.returncode == 0
    else:
        try:
            return os.geteuid() == 0
        except Exception:
            return False
