# `vanta` Python Package

This directory contains the core implementation of **VANTA** (Virtual Autonomous Network & Technical Analyst). 

## Directory Structure

```text
vanta/
├── main.py                 # CLI loop & event execution orchestrator
├── config.py               # Shared settings & environment loaders
│
├── agent/                  # LangChain & Ollama agent integrations
│   ├── agent.py            # ChatOllama construction & tool bindings
│   ├── memory.py           # Sliding-window conversation memory
│   ├── prompts.py          # System prompt & technician rules
│   └── schemas.py          # Diagnostic data validation schemas
│
├── tools/                  # Read-only systems diagnostics collectors
│   ├── system.py           # OS, platform, and basic environment specs
│   ├── hardware.py         # Motherboard, GPU, battery, and sensors
│   ├── cpu.py              # Per-core utilization & frequency analytics
│   ├── memory.py           # RAM pagefile & allocation limits
│   ├── processes.py        # High-usage active processes
│   ├── storage.py          # Partitions, volumes, and capacity checking
│   ├── network.py          # DNS status, WAN ping, & gateways
│   ├── services.py         # Automatic Windows services tracker
│   ├── startup.py          # Registry boot startup items
│   ├── software.py         # Registry-based installed software inventory
│   └── logs.py             # Event viewer errors & warning scanner
│
├── diagnostics/            # Deterministic & rule-based scanners
│   ├── health.py           # System health calculator & score weightings
│   └── engine.py           # Rules engine fallback & LLM dispatching
│
├── actions/                # OS-modifying repair executions
│   ├── executor.py         # Subprocess commands (e.g., net start, ipconfig)
│   ├── registry.py         # Whitelist map of action handlers & risk parameters
│   └── permissions.py      # Admin verification utilities
│
├── database/               # Local persistence layers
│   └── history.py          # SQLite database session & audit logs
│
├── ui/                     # Rich terminal layout and visual styling
│   ├── terminal.py         # Styled inputs & console wrapper
│   ├── panels.py           # Custom report templates & interactive prompts
│   ├── animations.py       # ASCII banner & boot loaders
│   └── theme.py            # Themes (Amber Glow, Solar Flare, etc.)
│
└── tests/                  # Automated pytest testing suite
```

## Key Components

### 1. Main Entrypoint ([main.py](file:///e:/Darsh/Langchain_agent/vanta/main.py))
- Coordinates the main CLI loop, handling user commands (`scan`, `status`, `exit`, etc.) and processing natural language inputs.
- Invokes the LangChain agent for LLM-driven query resolution or uses the rules-engine fallback when Ollama is offline.
- Renders an interactive, theme-based UI using `rich`.

### 2. Configuration ([config.py](file:///e:/Darsh/Langchain_agent/vanta/config.py))
- Parses environment variables from the root `.env` file.
- Exposes:
  - `VANTA_MODEL`: LLM identifier (defaults to `gemma4:31b-cloud`).
  - `OLLAMA_BASE_URL`: Ollama local instance URL.
  - `VANTA_SAFE_MODE`: Boolean determining if OS-modifying commands are permitted.
  - `DB_PATH`: SQLite memory database path.

### 3. Agent Subpackage ([agent/](file:///e:/Darsh/Langchain_agent/vanta/agent/))
- Builds the `ChatOllama` agent and binds diagnostic/repair tools.
- Implements `ConversationMemory` to track conversational context with sliding limits to prevent context overflow.

### 4. Diagnostics & Tools ([tools/](file:///e:/Darsh/Langchain_agent/vanta/tools/) & [diagnostics/](file:///e:/Darsh/Langchain_agent/vanta/diagnostics/))
- Diagnostic plugins in `tools/` gather system telemetry using native Python/Windows APIs.
- The `diagnostics/engine.py` runs checks sequentially, producing a structured scan report.
- The `health.py` module uses heuristic math to calculate a health score from 0-100 based on warnings.

### 5. Repair Actions ([actions/](file:///e:/Darsh/Langchain_agent/vanta/actions/))
- Safe, non-arbitrary repair routines that require explicit user verification when Safe Mode is disabled.
- Actions list:
  - `restart_service`: Restarts a stopped automatic Windows service.
  - `clear_temp_files`: Wipes user/system temp directories.
  - `disable_startup_app`: Disables application startup items.
  - `flush_dns`: Resets the Windows DNS resolver cache.

### 6. Persistent Database ([database/](file:///e:/Darsh/Langchain_agent/vanta/database/))
- Uses a local SQLite file to store the session metadata, scan findings, applied recommendations, and user repair choices.

### 7. Rich User Interface ([ui/](file:///e:/Darsh/Langchain_agent/vanta/ui/))
- Styled panels, animated CLI entry, and theme loader supporting custom configurations such as `Amber Glow` and `Solar Flare`.

---

## Developer Guide

### Adding a Diagnostic Tool
1. Create a function wrapped with the LangChain `@tool` decorator under `vanta/tools/`.
2. Define a clear docstring describing what system info the tool retrieves so the LLM knows when to call it.
3. Import the tool function inside [agent.py](file:///e:/Darsh/Langchain_agent/vanta/agent/agent.py) and add it to the `ALL_TOOLS` list.

### Registering a New Action
1. Write the target repair method inside [executor.py](file:///e:/Darsh/Langchain_agent/vanta/actions/executor.py).
2. Register the action name, risks (`LOW`, `MEDIUM`, `HIGH`), and the execution callback inside [registry.py](file:///e:/Darsh/Langchain_agent/vanta/actions/registry.py).
3. Bind the action tool using a validator wrapper in [agent.py](file:///e:/Darsh/Langchain_agent/vanta/agent/agent.py) to handle user confirmations and `VANTA_SAFE_MODE` checks.
