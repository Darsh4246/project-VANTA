import sys
from rich.console import Console
from rich.text import Text
from vanta.ui.theme import get_theme

console = Console()

def get_input(prompt_text: str) -> str:
    """Prompt the user for terminal input with a styled prompt."""
    theme = get_theme()
    console.print(Text("-" * 65, style="dim"))
    console.print(
        Text("VANTA", style=f"bold {theme['primary']}") + Text(" > ", style=theme['secondary']),
        end=""
    )
    try:
        ans = sys.stdin.readline().strip()
        return ans
    except (KeyboardInterrupt, EOFError):
        return "exit"
