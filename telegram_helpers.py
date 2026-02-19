#!/usr/bin/env python3
"""
Telegram Bot Helper Functions - Base Template

Pure-Python helpers for the Telegram listener daemon.
No MCP or Claude dependencies — only stdlib, requests, and your APIs.

This is a minimal template. Add your own integrations by following
the pattern below, or use the templates/helper_template.py for reference.

Built by: x.com/@shaneswrld_ | github.com/shane9coy
"""

import os
import json
from datetime import datetime, date
from pathlib import Path

import requests
from dotenv import load_dotenv

# ── Config ──────────────────────────────────────────────────
PROJECT_DIR = Path(__file__).parent
load_dotenv(PROJECT_DIR / ".env")

# Add your API keys here
# MY_API_KEY = os.getenv("MY_API_KEY", "")

# User profile path (optional, for personalized responses)
PROFILE_PATH = PROJECT_DIR / ".claude" / "user_profile.json"


def _load_profile():
    """Load user profile for personalized responses."""
    try:
        return json.loads(PROFILE_PATH.read_text())
    except Exception:
        return {}


# ═══════════════════════════════════════════════════════════
#  EXAMPLE HELPERS
# ═══════════════════════════════════════════════════════════

def get_status():
    """
    Basic status check helper.
    
    Returns:
        str: Formatted status message
    """
    return f"**Bot Status**\nRunning since: {datetime.now().strftime('%Y-%m-%d %H:%M')}"


def get_weather_example():
    """
    Example weather helper using Open-Meteo (free, no API key needed).
    
    Returns:
        str: Formatted weather message
    """
    profile = _load_profile()
    loc = profile.get("location", {})
    lat = loc.get("latitude", 41.4489)
    lon = loc.get("longitude", -82.708)
    name = loc.get("name", "Unknown")
    
    try:
        r = requests.get("https://api.open-meteo.com/v1/forecast", params={
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,weather_code",
            "temperature_unit": "fahrenheit",
            "timezone": "auto",
        }, timeout=10)
        data = r.json().get("current", {})
        temp = data.get("temperature_2m", "?")
        code = data.get("weather_code", 0)
        
        # WMO weather codes
        WMO = {
            0: "Clear", 1: "Mostly clear", 2: "Partly cloudy", 3: "Overcast",
            45: "Foggy", 51: "Light drizzle", 61: "Rain", 71: "Snow",
            80: "Showers", 95: "Thunderstorm"
        }
        cond = WMO.get(code, "Unknown")
        
        return f"**Weather — {name}**\n{temp}°F\n{cond}"
    except Exception as e:
        return f"Weather unavailable: {e}"


# ═══════════════════════════════════════════════════════════
#  YOUR CUSTOM HELPERS
# ═══════════════════════════════════════════════════════════

# Add your custom helpers below following this pattern:
#
# def get_my_service():
#     """
#     Description of what this helper does.
#     
#     Returns:
#         str: Formatted response message
#     """
#     # Your implementation here
#     return "**My Service**\nResult here"
#
# Then import and use it in telegram_listener.py

def get_help():
    """Return available commands."""
    return """**Available Commands**

/status - Bot status
/weather - Current weather
/help - Show this message

_Add more commands by editing telegram_helpers.py_
"""
