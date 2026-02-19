# Telegram Bot Guide

Complete guide for the Telegram bot template: always-listening daemon, command reference, server management, and building custom integrations.

---

## Quick Reference — Server Management

### Start / Stop / Status

```bash
# Check if listener is running
python telegram_listener.py --status

# Start in foreground (see logs live)
python telegram_listener.py

# Start as background daemon
python telegram_listener.py --daemon

# Stop the running listener
python telegram_listener.py --stop

# Enter sleep mode (no responses, only scheduled alerts)
python telegram_listener.py --sleep

# Wake from sleep mode
python telegram_listener.py --wake
```

### After Updating `.env` Variables

The listener loads environment variables at startup. If you change `.env`, **restart**:

```bash
python telegram_listener.py --stop && python telegram_listener.py --daemon
```

### Logs

```bash
# Live tail of listener logs
tail -f logs/telegram_listener.log

# Check recent activity
tail -50 logs/telegram_listener.log
```

### Run as macOS Launch Agent (always-on)

Create `~/Library/LaunchAgents/com.yourname.telegram-listener.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.yourname.telegram-listener</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/path/to/Telegram/telegram_listener.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>WorkingDirectory</key>
    <string>/path/to/Telegram</string>
    <key>StandardOutPath</key>
    <string>/path/to/Telegram/logs/telegram_listener.log</string>
    <key>StandardErrorPath</key>
    <string>/path/to/Telegram/logs/telegram_listener_error.log</string>
</dict>
</plist>
```

```bash
# Load (start at login)
launchctl load ~/Library/LaunchAgents/com.yourname.telegram-listener.plist

# Unload (stop)
launchctl unload ~/Library/LaunchAgents/com.yourname.telegram-listener.plist

# Check status
launchctl list | grep telegram
```

### PID & State Files

| File | Purpose |
|------|---------|
| `/tmp/telegram_listener.pid` | Running process ID |
| `/tmp/telegram_listener_state.json` | Sleep/wake state |
| `/tmp/telegram_agent_queue.json` | Queued commands for agent pickup |

---

## Architecture

```
┌──────────────────┐          ┌────────────────────────┐
│  Telegram User   │◀────────▶│  telegram_listener.py  │
│  (phone/desktop) │  Telethon│  (Telegram Bot daemon) │
└──────────────────┘  Bot API │                        │
                               │  route_command()       │
                               │    ├─ handle_tasks()   │
                               │    ├─ handle_goals()   │
                               │    ├─ handle_weather() │
                               │    └─ [your commands]  │
                               └──────────┬─────────────┘
                                          │ imports
                               ┌──────────▼─────────────┐
                               │  telegram_helpers.py   │
                               │  (pure Python engine)  │
                               │                        │
                               │  Add your services:    │
                               │  • API integrations    │
                               │  • Data processing     │
                               │  • Custom logic        │
                               └──────────┬─────────────┘
                                          │ HTTP
                               ┌──────────▼─────────────┐
                               │  External APIs         │
                               │  • Open-Meteo (weather)│
                               │  • Your APIs here      │
                               └────────────────────────┘
```

### Key Files

| File | Purpose |
|------|---------|
| `telegram_listener.py` | Bot daemon — Telethon client, event handler, command router, scheduled alerts |
| `telegram_helpers.py` | Pure-Python helpers — add your custom integrations here |
| `templates/helper_template.py` | Full integration pattern reference |
| `.env` | API keys and credentials |
| `.claude/user_profile.json` | User profile (preferences, daily tracker, telegram config) |

---

## Built-in Commands

Send these to your bot on Telegram.

### System

| Command | Description |
|---------|-------------|
| `/help` | Full command list |
| `/status` | Listener mode, pending tasks, PID |
| `/weather` | Current weather (from Open-Meteo) |
| `sleep` / `goodnight` | Enter sleep mode (only scheduled alerts) |
| `wake` / `good morning` | Exit sleep mode |

### Tasks & Goals

| Command | Description |
|---------|-------------|
| `/tasks` | Today's pending tasks |
| `add task: <text>` | Add a new task |
| `done: <text>` or `done <#>` | Complete a task by name or number |
| `/goals` | Active goals |
| `add goal: <text>` | Add a new goal |
| `/progress` | Today's stats (pending, completed, streak) |

---

## Building Custom Integrations

### Quick Pattern

1. **Add helper function** in `telegram_helpers.py`:

```python
def get_my_service(query=None):
    """
    Fetch data from your API.
    
    Args:
        query: Optional search parameter
        
    Returns:
        str: Formatted Markdown response
    """
    # Your implementation
    return "**My Service**\nResult here"
```

2. **Import in** `telegram_listener.py`:

```python
from telegram_helpers import get_my_service
```

3. **Add command handler** in `route_command()`:

```python
if lower.startswith("/myservice"):
    query = text.split(maxsplit=1)[1] if len(text.split()) > 1 else None
    return get_my_service(query)
```

### Template Reference

See `templates/helper_template.py` for a complete integration example with:
- API client pattern
- Error handling
- Response formatting
- User profile integration
- Scheduled alerts

---

## Scheduled Alerts

The listener runs two automatic alerts (configurable in `user_profile.json` → `telegram`):

### Morning Brief (8:00 AM)

Sends weather + today's tasks + active goals. Controlled by `telegram.morning_brief` in profile.

### Evening Check-In (8:00 PM default)

Sends completed vs pending tasks, updates streak counter. Time set by `telegram.goal_checkin_time` in profile.

### Sleep Mode

When sleeping (`sleep` / `goodnight`), the bot:
- Ignores all commands except `wake`, `good morning`, `status`
- Still sends scheduled alerts (morning brief, evening check-in)

---

## Configuration

### Environment Variables (`.env`)

```env
# Required - Get from @BotFather
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz

# Required - Get from @userinfobot
TELEGRAM_BOT_USER_ID=123456789

# Required - Get from my.telegram.org
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=your_api_hash_here

# Optional - Add your own API keys
# MY_SERVICE_API_KEY=your_key_here
```

### `user_profile.json` → `telegram` section

```json
{
  "telegram": {
    "chat_id": null,
    "notifications_enabled": true,
    "morning_brief": true,
    "task_reminders": true,
    "goal_checkin_time": "20:00",
    "always_listening": true
  },
  "location": {
    "name": "Your City",
    "latitude": 41.4489,
    "longitude": -82.708
  }
}
```

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `chat_id` | int | — | Your Telegram user ID (for sending notifications) |
| `notifications_enabled` | bool | true | Master toggle for all notifications |
| `morning_brief` | bool | true | Send 8 AM morning brief |
| `task_reminders` | bool | true | Remind about pending tasks |
| `goal_checkin_time` | string | "20:00" | Time for evening check-in (HH:MM) |
| `always_listening` | bool | true | Whether the daemon should be running |

---

## Setup Instructions

### Step 1: Get Telegram API Credentials

1. Visit https://my.telegram.org/apps
2. Sign in with your phone number
3. Create a new application
4. Copy `api_id` and `api_hash`

### Step 2: Create a Bot via BotFather

1. Message @BotFather on Telegram
2. `/newbot` → Choose a name and username
3. Copy the bot token

### Step 3: Get Your User ID

Message @userinfobot on Telegram — it replies with your numeric ID.

### Step 4: Configure Environment

Create `.env` file:

```env
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_BOT_USER_ID=your_user_id
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
```

### Step 5: Start the Bot

```bash
mkdir -p logs
python telegram_listener.py --daemon
```

---

## Troubleshooting

### Bot Not Responding

1. Check if listener is running:
   ```bash
   python telegram_listener.py --status
   ```

2. Check logs for errors:
   ```bash
   tail logs/telegram_listener.log
   ```

3. Verify `.env` credentials are correct

### Permission Errors

```bash
mkdir -p logs
chmod 755 logs
```

### Import Errors

```bash
pip install -r requirements.txt
```

### Session Errors

If you get session-related errors, delete the session file and restart:

```bash
rm ~/mcp-servers/telegram-mcp/telegram_bot.session*
python telegram_listener.py --daemon
```

---

## Privacy Mode

To make a private Telegram bot public (read all messages in groups):

1. Open @BotFather on Telegram
2. Send `/mybots` and select your bot
3. Choose **Bot Settings** → **Group Privacy**
4. Select **Disable**

**Note:** By default, bots only see messages that mention them or commands.

---

## For AI Assistants

If you're an AI assistant helping set up this bot, use the `telegram-builder` skill for detailed integration guidance.

### Setup Checklist

```markdown
- [ ] Verify Python 3.8+ is installed
- [ ] Run `pip install -r requirements.txt`
- [ ] Copy `.env.example` to `.env`
- [ ] Guide user to get Telegram credentials
- [ ] Create logs directory: `mkdir -p logs`
- [ ] Start daemon: `python telegram_listener.py --daemon`
- [ ] Verify: `python telegram_listener.py --status`
- [ ] Test: Send `/help` to the bot
```
