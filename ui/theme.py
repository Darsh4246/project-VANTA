import os
import sqlite3
from vanta.config import DB_PATH

THEMES = {
    "amber_glow": {
        "name": "Amber Glow",
        "desc": "A premium theme utilizing glowing orange, amber, and gold accents",
        "primary": "#f97316",     # Orange
        "secondary": "#fbbf24",   # Amber / Gold
        "highlight": "#f59e0b",   # Rich Yellow
        "accent": "#ef4444",      # Warm Red
        "success": "#10b981",     # Emerald
        "spinner_type": "arc"
    },
    "solar_flare": {
        "name": "Solar Flare",
        "desc": "A burning orange, gold, and amber palette",
        "primary": "#d97706",     # Dark Amber
        "secondary": "#f59e0b",   # Amber
        "highlight": "#facc15",   # Yellow
        "accent": "#ff007f",      # Neon pink/red flare
        "success": "#22c55e",     # Green
        "spinner_type": "dots"
    },
    "cyber_rust": {
        "name": "Cyber Rust",
        "desc": "A rusty industrial theme of copper and safety orange",
        "primary": "#ea580c",     # Rust orange
        "secondary": "#ca8a04",   # Dark gold
        "highlight": "#eab308",   # Safety yellow
        "accent": "#9a3412",      # Deep brown/red
        "success": "#16a34a",     # Forest Green
        "spinner_type": "line"
    }
}

active_theme_key = "amber_glow"

def get_theme():
    """Retrieve current active theme dictionary."""
    return THEMES.get(active_theme_key, THEMES["amber_glow"])

def get_theme_key():
    return active_theme_key

def load_active_theme():
    """Load settings from DB and update current active theme."""
    global active_theme_key
    try:
        with sqlite3.connect(DB_PATH) as con:
            con.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
            row = con.execute("SELECT value FROM settings WHERE key = 'theme'").fetchone()
            if row and row[0] in THEMES:
                active_theme_key = row[0]
    except Exception:
        pass

def save_active_theme(theme_name):
    """Save the theme name to SQLite and set active theme."""
    global active_theme_key
    if theme_name in THEMES:
        active_theme_key = theme_name
        try:
            with sqlite3.connect(DB_PATH) as con:
                con.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
                con.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('theme', ?)", (theme_name,))
                con.commit()
        except Exception:
            pass
