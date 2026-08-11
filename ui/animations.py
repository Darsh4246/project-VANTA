import time
from rich.console import Console, Group
from rich.align import Align
from rich.panel import Panel
from rich.text import Text
from vanta.ui.theme import get_theme

LOGO = r"""
██╗   ██╗ █████╗ ███╗   ██╗████████╗ █████╗ 
██║   ██║██╔══██╗████╗  ██║╚══██╔══╝██╔══██╗
██║   ██║███████║██╔██╗ ██║   ██║   ███████║
╚██╗ ██╔╝██╔══██║██║╚██╗██║   ██║   ██╔══██║
 ╚████╔╝ ██║  ██║██║ ╚████║   ██║   ██║  ██║
  ╚═══╝  ╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝   ╚═╝  ╚═╝
"""

SUBTITLE = "VIRTUAL AUTONOMOUS NETWORK & TECHNICAL ANALYST"

def show_logo(console: Console):
    theme = get_theme()
    logo_text = Text(LOGO, style=f"bold {theme['primary']}")
    sub_text = Text(SUBTITLE, style=f"bold {theme['secondary']}")
    
    panel_content = Group(
        Align.center(logo_text),
        Align.center(Text("")),
        Align.center(sub_text)
    )
    
    console.print(
        Panel(
            panel_content,
            border_style=theme['secondary'],
            expand=False,
            padding=(1, 4)
        )
    )

def run_startup_animation(console: Console):
    theme = get_theme()
    show_logo(console)
    console.print()
    
    console.print(f"[bold {theme['primary']}]Initializing VANTA...[/bold {theme['primary']}]")
    console.print()
    
    steps = [
        ("Loading system interface", 0.3),
        ("Initializing diagnostics engine", 0.4),
        ("Loading hardware subsystem", 0.3),
        ("Loading network subsystem", 0.4),
        ("Loading AI engine", 0.3)
    ]
    
    for desc, delay in steps:
        console.print(f"  [bold {theme['highlight']}]◉[/bold {theme['highlight']}] {desc}...", end="\r")
        time.sleep(delay)
        console.print(f"  [bold {theme['success']}]✓[/bold {theme['success']}] {desc}   ")
        
    time.sleep(0.2)
    console.print(f"\n[bold {theme['success']}]✓ VANTA online[/bold {theme['success']}]")
    console.print()
