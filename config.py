import os
from pathlib import Path
from dotenv import load_dotenv

# Resolve workspace directories
ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

# Check both VANTA_MODEL and OLLAMA_MODEL for backwards compatibility
VANTA_MODEL = os.getenv("VANTA_MODEL", os.getenv("OLLAMA_MODEL", "gemma4:31b-cloud"))
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
VANTA_SAFE_MODE = os.getenv("VANTA_SAFE_MODE", "true").lower() in ("true", "1", "yes")

WORKSPACE_DIR = Path(os.getenv("WORKSPACE_DIR", "./workspace")).resolve()
WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = WORKSPACE_DIR / "vanta_memory.sqlite3"
