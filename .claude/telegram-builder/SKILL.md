---
name: telegram-builder
triggers: "add telegram command, new telegram integration, build telegram bot, telegram helper, add bot command, telegram service"
description: "Guide for building new Telegram bot integrations, commands, and helper functions. Use when the user wants to extend their Telegram bot with new services or APIs."
---

# Telegram Integration Builder Skill

Activate when the user wants to add new commands, integrations, or services to their Telegram bot.

## Overview

This skill guides you through building new Telegram bot integrations following the project's established patterns.

## Project Structure

```
Telegram/
├── telegram_listener.py      # Main daemon - handles incoming messages
├── telegram_helpers.py       # Helper functions - add new services here
├── templates/
│   └── helper_template.py    # Full integration pattern reference
├── .env                      # API credentials
├── .claude/
│   └── user_profile.json     # User preferences
└── logs/
    └── telegram_listener.log
```

## Integration Pattern

### Step 1: Add Helper Function

Edit `telegram_helpers.py` to add your service:

```python
def get_my_service(query=None):
    """
    Description of what this helper does.
    
    Args:
        query: Optional search parameter
        
    Returns:
        str: Formatted Markdown response
    """
    # 1. Load user profile if needed
    profile = _load_profile()
    
    # 2. Make API call or process data
    try:
        r = requests.get("https://api.example.com/data", 
                        params={"q": query},
                        timeout=10)
        data = r.json()
    except Exception as e:
        return f"**Error**\n{e}"
    
    # 3. Format response as Markdown
    lines = ["**My Service Results**", ""]
    for item in data.get("items", [])[:5]:
        lines.append(f"• {item.get('name')}: {item.get('value')}")
    
    return "\n".join(lines)
```

### Step 2: Import in Listener

Add to `telegram_listener.py` imports (around line 37):

```python
from telegram_helpers import (
    # ... existing imports ...
    get_my_service,  # Add your new helper
)
```

### Step 3: Add Command Handler

Find the `handle_message()` function in `telegram_listener.py` and add:

```python
elif text.startswith("/myservice"):
    parts = text.split(maxsplit=1)
    query = parts[1] if len(parts) > 1 else None
    result = get_my_service(query)
    await event.reply(result)
```

### Step 4: Add API Credentials

Add to `.env`:

```env
MY_SERVICE_API_KEY=your_key_here
```

Reference in `telegram_helpers.py`:

```python
MY_SERVICE_API_KEY = os.getenv("MY_SERVICE_API_KEY", "")
```

### Step 5: Test

```bash
# Restart the daemon
python telegram_listener.py --stop
python telegram_listener.py --daemon

# Check logs
tail -f logs/telegram_listener.log
```

## Response Formatting

Use Markdown for rich formatting:

```python
# Headers
"**Bold Header**"

# Lists
"• Item 1\n• Item 2"

# Status indicators
"✅ Success"
"❌ Error"
"⏳ Loading..."
"🔄 Processing..."

# Code blocks
"```\ncode here\n```"

# Links
"[Link Text](https://example.com)"
```

## Common Patterns

### API Integration

```python
def get_api_data(endpoint, params=None):
    """Generic API client pattern."""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    try:
        r = requests.get(
            f"{API_BASE}/{endpoint}",
            headers=headers,
            params=params,
            timeout=10
        )
        r.raise_for_status()
        return r.json()
    except requests.exceptions.HTTPError as e:
        return None, f"API error: {e.response.status_code}"
    except Exception as e:
        return None, f"Error: {e}"
```

### User Profile Integration

```python
def get_personalized_data():
    """Use user profile for personalization."""
    profile = _load_profile()
    
    # Get user preferences
    location = profile.get("location", {})
    preferences = profile.get("preferences", {})
    
    # Use in API calls
    lat = location.get("latitude", 0)
    lon = location.get("longitude", 0)
    
    # Return personalized response
    return f"**Personalized for {location.get('name', 'You')}**\n..."
```

### Scheduled Alerts

Add to `telegram_listener.py` in the scheduled alerts section:

```python
async def send_my_alert():
    """Send scheduled alert for your service."""
    result = get_my_service()
    await client.send_message(USER_ID, result)

# Add to scheduler (find the scheduling section)
schedule.every().day.at("09:00").do(send_my_alert)
```

## Template Reference

For a complete integration example, see:
- [`templates/helper_template.py`](templates/helper_template.py) - Full integration pattern

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Command not recognized | Check import in telegram_listener.py |
| No response | Check logs: `tail -f logs/telegram_listener.log` |
| API error | Verify credentials in .env |
| Import error | Ensure helper is exported from telegram_helpers.py |

## Best Practices

1. **Error Handling**: Always wrap API calls in try/except
2. **Timeouts**: Use timeout parameter for all requests
3. **Rate Limiting**: Respect API rate limits
4. **Caching**: Cache responses when appropriate
5. **User Feedback**: Always return something, even on error
6. **Logging**: Add logging for debugging

## Example: Complete Integration

```python
# In telegram_helpers.py

WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "")

def get_weather(location=None):
    """Get weather for a location."""
    profile = _load_profile()
    
    # Use profile location if not specified
    if not location:
        loc = profile.get("location", {})
        location = loc.get("name", "New York")
    
    try:
        r = requests.get(
            "https://api.weatherapi.com/v1/current.json",
            params={"key": WEATHER_API_KEY, "q": location},
            timeout=10
        )
        data = r.json()
        
        temp = data["current"]["temp_f"]
        cond = data["current"]["condition"]["text"]
        
        return f"**Weather — {location}**\n{temp}°F\n{cond}"
    except Exception as e:
        return f"**Weather Error**\n{e}"

# In telegram_listener.py - add import
from telegram_helpers import get_weather

# In handle_message() - add handler
elif text.startswith("/weather"):
    parts = text.split(maxsplit=1)
    location = parts[1] if len(parts) > 1 else None
    result = get_weather(location)
    await event.reply(result)