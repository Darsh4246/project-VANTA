```text
██╗   ██╗ █████╗ ███╗   ██╗████████╗ █████╗ 
██║   ██║██╔══██╗████╗  ██║╚══██╔══╝██╔══██╗
██║   ██║███████║██╔██╗ ██║   ██║   ███████║
╚██╗ ██╔╝██╔══██║██║╚██╗██║   ██║   ██╔══██║
 ╚████╔╝ ██║  ██║██║ ╚████║   ██║   ██║  ██║
  ╚═══╝  ╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝   ╚═╝  ╚═╝

  VIRTUAL AUTONOMOUS NETWORK & TECHNICAL ANALYST
```

Welcome to **VANTA** (Virtual Autonomous Network & Technical Analyst). VANTA is a state-of-the-art AI systems technician and diagnostic console designed to inspect your hardware, operating system, running processes, drivers, and network connectivity using plain English and automated scans.

---

## 🚀 How to Run VANTA

To start VANTA, make sure you have Python 3.12+ and Ollama installed.

1. **Start Ollama** (required for Natural Language Mode):
   Ensure your local Ollama server is running and you have downloaded the required model:
   ```bash
   ollama run gemma4:31b-cloud
   ```
   *(Or the model specified in your environment config).*

2. **Launch the Console:**
   - On **Windows**, double-click the **`run_agent.bat`** script in the project root, or execute:
     ```cmd
     run_agent.bat
     ```
   - Alternatively, activate the virtual environment and run manually:
     ```bash
     .venv\Scripts\activate
     set PYTHONPATH=%CD%
     python vanta/main.py
     ```

---

## 🛠 How to Use VANTA

Once the terminal interface loads, you can interact with VANTA in two ways:

### 1. Ask Questions in Plain English (Natural Language Mode)
Just type what you'd like to check or fix, and the AI agent will automatically run the appropriate diagnostics tools:
* *“Why is my computer running so slow?”*
* *“Check if my fingerprint reader is installed and working.”*
* *“What applications are taking up all my RAM?”*
* *“Clean up temporary files on my hard drive.”*
* *“Are there any stopped automatic services?”*

### 2. Run Direct CLI Shortcuts
You can type direct commands for immediate diagnostics:
* `scan` — Execute a comprehensive, multi-point system health scan.
* `status` — Show system engine status, model info, and safe-mode state.
* `devices` — List system PnP devices, drivers, and biometric sensors.
  * `devices biometric` — Specifically lists biometric hardware (like fingerprint readers).
  * `devices problematic` — Shows only devices reporting warning/error statuses.
  * `devices <query>` — Search for a specific device or driver (e.g., `devices goodix`).
* `hardware` — Display motherboard, GPU, and system temperature information.
* `cpu` — Print live utilization metrics and per-core usage.
* `memory` — Show RAM utilization and pagefile details.
* `processes` — Display processes consuming the most resources.
* `storage` — Inspect hard drive partitions and capacity.
* `network` — Test gateway connections, DNS latency, and internet reachability.
* `services` — Check automatic Windows services that are currently stopped.
* `startup` — List programs that run automatically on system boot.
* `software` — Search and inventory installed applications.
* `logs` — Summarize critical errors and warnings from Windows Event Logs.
* `history` — View audit trails of past diagnostic queries and recommendations.
* `settings` — Change console color themes (e.g. `Solar Flare`, `Amber Glow`).
* `clear` — Clear current conversation context memory.
* `about` — Display project details and credits.
* `exit` — Suspends and closes the diagnostics session.

---

## 💻 Developer's Notes

### Project Directory Structure

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
│   ├── devices.py          # Plug & Play hardware devices & drivers list
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

### Adding a Diagnostic Tool
1. Create a tool method wrapped with the LangChain `@tool` decorator under `vanta/tools/`.
2. Define a descriptive docstring explaining what telemetry is retrieved. The AI agent relies on this docstring to understand when to invoke it.
3. Import the tool function inside [agent.py](file:///e:/Darsh/Langchain_agent/vanta/agent/agent.py) and append it to the `ALL_TOOLS` registry list.

### Registering a Repair Action
1. Write the repair logic in [executor.py](file:///e:/Darsh/Langchain_agent/vanta/actions/executor.py).
2. Register the command name, danger classification (`LOW`, `MEDIUM`, `HIGH`), and the execution callback inside [registry.py](file:///e:/Darsh/Langchain_agent/vanta/actions/registry.py).
3. Bind the action tool using a validator wrapper in [agent.py](file:///e:/Darsh/Langchain_agent/vanta/agent/agent.py) to manage user approval triggers and `VANTA_SAFE_MODE` protection flags.
