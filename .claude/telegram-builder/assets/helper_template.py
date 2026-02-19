#!/usr/bin/env python3
"""
Telegram Helper Template - Full Integration Pattern

This template shows the complete pattern for adding a new service
integration to your Telegram bot.

Copy this file and modify for your specific API/service.

Steps:
1. Add your API configuration
2. Implement the helper function(s)
3. Import in telegram_listener.py
4. Add command handler in telegram_listener.py

Built by: x.com/@shaneswrld_ | github.com/shane9coy
"""

import os
import json
from datetime import datetime, date
from pathlib import Path

import requests
from dotenv import load_dotenv

# ── Configuration ────────────────────────────────────────────
PROJECT_DIR = Path(__file__).parent
load_dotenv(PROJECT_DIR / ".env")

# Add your API credentials in .env and reference here
# Example:
# MY_API_KEY = os.getenv("MY_API_KEY", "")
# MY_API_BASE = "https://api.example.com"

PROFILE_PATH = PROJECT_DIR / ".claude" / "user_profile.json"


def _load_profile():
    """Load user profile for personalized responses."""
    try:
        return json.loads(PROFILE_PATH.read_text())
    except Exception:
        return {}


# ═══════════════════════════════════════════════════════════
#  API CLIENT
# ═══════════════════════════════════════════════════════════

def _api_request(endpoint, params=None):
    """
    Make authenticated request to your API.
    
    Args:
        endpoint: API endpoint path
        params: Query parameters dict
        
    Returns:
        dict: JSON response or None on error
    """
    # Example implementation - modify for your API
    # headers = {
    #     "Authorization": f"Bearer {MY_API_KEY}",
    #     "Content-Type": "application/json",
    # }
    # 
    # try:
    #     r = requests.get(
    #         f"{MY_API_BASE}/{endpoint}",
    #         headers=headers,
    #         params=params,
    #         timeout=10
    #     )
    #     r.raise_for_status()
    #     return r.json()
    # except Exception as e:
    #     print(f"API error: {e}")
    #     return None
    pass


# ═══════════════════════════════════════════════════════════
#  HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════

def get_service_status():
    """
    Check service connection status.
    
    Returns:
        str: Formatted status message
    """
    # Example:
    # data = _api_request("status")
    # if data:
    #     return f"**Service Status**\nConnected: {data.get('status', 'unknown')}"
    # return "**Service Status**\n❌ Connection failed"
    return "**Service Status**\nNot configured. Add your API credentials."


def get_service_data(query=None):
    """
    Fetch data from your service.
    
    Args:
        query: Optional search/query parameter
        
    Returns:
        str: Formatted response message
    """
    profile = _load_profile()
    
    # Example implementation:
    # params = {"q": query} if query else None
    # data = _api_request("data", params)
    # 
    # if not data:
    #     return "No data available."
    # 
    # items = data.get("items", [])
    # lines = [f"**Results for: {query or 'all'}**", ""]
    # 
    # for item in items[:5]:  # Limit to 5 results
    #     name = item.get("name", "Unknown")
    #     value = item.get("value", "")
    #     lines.append(f"• {name}: {value}")
    # 
    # return "\n".join(lines)
    
    return f"**Service Data**\nQuery: {query or 'none'}\nConfigure your API to fetch real data."


def get_service_item(item_id):
    """
    Get details for a specific item.
    
    Args:
        item_id: Item identifier
        
    Returns:
        str: Formatted item details
    """
    # Example:
    # data = _api_request(f"items/{item_id}")
    # if not data:
    #     return f"Item {item_id} not found."
    # 
    # return f"""**{data.get('name', 'Unknown')}**
    # 
    # ID: {item_id}
    # Status: {data.get('status', 'unknown')}
    # Created: {data.get('created_at', 'unknown')}
    # """
    
    return f"**Item {item_id}**\nConfigure your API to fetch real data."


def perform_action(action, target=None):
    """
    Perform an action on your service.
    
    Args:
        action: Action to perform (e.g., 'create', 'delete', 'update')
        target: Target item/identifier
        
    Returns:
        str: Action result message
    """
    # Example:
    # if action == "create":
    #     result = _api_request("items", {"action": "create"})
    #     return f"✅ Created: {result.get('id', 'unknown')}"
    # elif action == "delete" and target:
    #     result = _api_request(f"items/{target}", {"action": "delete"})
    #     return f"🗑️ Deleted: {target}"
    # 
    # return f"Unknown action: {action}"
    
    return f"**Action: {action}**\nTarget: {target or 'none'}\nConfigure your API to perform actions."


# ═══════════════════════════════════════════════════════════
#  FORMATTING HELPERS
# ═══════════════════════════════════════════════════════════

def _format_list(items, title="Items"):
    """Format a list of items for Telegram display."""
    lines = [f"**{title}**", ""]
    for item in items:
        lines.append(f"• {item}")
    return "\n".join(lines)


def _format_error(message):
    """Format an error message."""
    return f"❌ **Error**\n{message}"


def _format_success(message):
    """Format a success message."""
    return f"✅ **Success**\n{message}"


# ═══════════════════════════════════════════════════════════
#  HELP TEXT
# ═══════════════════════════════════════════════════════════

def get_help():
    """Return help text for this service's commands."""
    return """**My Service Commands**

/service - Check connection status
/service data [query] - Fetch data
/service item <id> - Get item details
/service <action> [target] - Perform action

_Replace 'service' with your command name in telegram_listener.py_
"""


# ═══════════════════════════════════════════════════════════
#  INTEGRATION INSTRUCTIONS
# ═══════════════════════════════════════════════════════════

"""
INTEGRATION STEPS:

1. Copy this template to telegram_helpers.py or import it:
   from templates.helper_template import get_service_status, get_service_data

2. Add your API credentials to .env:
   MY_API_KEY=your_key_here

3. Add command handler in telegram_listener.py:

   # Add import at top:
   from telegram_helpers import get_service_status, get_service_data, get_help
   
   # Add handler in handle_message():
   elif text.startswith("/service"):
       parts = text.split(maxsplit=2)
       if len(parts) == 1:
           result = get_service_status()
       elif parts[1] == "data":
           query = parts[2] if len(parts) > 2 else None
           result = get_service_data(query)
       else:
           result = get_help()
       await event.reply(result)

4. Test your integration:
   - Start the bot: python telegram_listener.py --daemon
   - Send /service to your bot on Telegram

5. Customize:
   - Add more helper functions as needed
   - Add scheduled alerts in telegram_listener.py
   - Store user preferences in user_profile.json
"""
