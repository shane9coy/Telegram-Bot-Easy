---
name: telegram
triggers: "send telegram, telegram message, telegram listener, start daemon, stop daemon, telegram notification, push notification, telegram bot, @YourBot, telegram alert"
description: "Control the always-listening Telegram daemon, send messages, manage the task/goal bot, and configure scheduled alerts."
---

# Telegram Skill

Auto-activate for Telegram message sending, daemon control, or bot configuration.

## Setup Instructions (For CLI Agents)

When helping the user set up the Telegram bot, follow these steps:

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Create Environment File
Copy the template and help the user fill in credentials:
```bash
cp .env.example .env
```

**Required credentials (user must obtain):**

| Credential | How to Get |
|------------|------------|
| `TELEGRAM_BOT_TOKEN` | Message @BotFather on Telegram, use `/newbot` |
| `TELEGRAM_BOT_USER_ID` | Message @userinfobot on Telegram |
| `TELEGRAM_API_ID` | Go to https://my.telegram.org → API Development Tools |
| `TELEGRAM_API_HASH` | Go to https://my.telegram.org → API Development Tools |

### Step 3: Create Logs Directory
```bash
mkdir -p logs
```

### Step 4: Start the Bot
```bash
python telegram_listener.py --daemon
```

### Step 5: Verify Setup
```bash
python telegram_listener.py --status
```

---

## Daemon Control

| What | Command |
|------|---------|
| Start listener | `/telegram start` |
| Stop listener | `/telegram stop` |
| Status + PID | `/telegram status` |
| Sleep (alerts only) | `/telegram sleep` |
| Wake (full response) | `/telegram wake` |
| View logs | `/telegram logs` |

## Send Messages

```
Command 'telegram' (see below for command content) send "Your message here"
Command 'telegram' (see below for command content) brief          # Send morning briefing now
Command 'telegram' (see below for command content) alert "msg"    # System alert notification
```

## Architecture

Two-tier — daemon is standalone Python, cannot call Claude MCP directly:

| Tier | Mechanism | Commands |
|------|-----------|----------|
| **Direct** | Pure Python + API calls | tasks, goals, weather, status |
| **Queue** | Write to `/tmp/telegram_agent_queue.json` | complex queries |

## Key Files

- Script: `telegram_listener.py` + `telegram_helpers.py`
- PID: `/tmp/telegram_listener.pid`
- State: `/tmp/telegram_listener_state.json`
- Logs: `logs/telegram_listener.log`
- Queue: `/tmp/telegram_agent_queue.json`
- Template: `templates/helper_template.py`

## Config (user_profile.json → telegram)

```json
{ "chat_id": null, "notifications_enabled": true, "morning_brief": true,
  "task_reminders": true, "goal_checkin_time": "20:00", "always_listening": true }
```

---

## Building New Integrations

Use the `telegram-builder` skill for detailed guidance on adding new commands and services.

### Quick Pattern

1. **Add helper function** in `telegram_helpers.py`:
   ```python
   def get_my_service(query=None):
       """Fetch data from your API."""
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

See [`templates/helper_template.py`](templates/helper_template.py) for a complete integration example.

---

## Built-in Bot Commands

The user can send these commands directly to their bot:

### Tasks & Goals
| Command | Action |
|---------|--------|
| `/tasks` | Today's tasks |
| `add task: ...` | Add a task |
| `done: ...` / `done 1` | Complete a task |
| `/goals` | Active goals |
| `add goal: ...` | Add a goal |
| `/progress` | Today's stats + streak |

### System
| Command | Action |
|---------|--------|
| `/help` | Full command menu |
| `/status` | Listener + system health |
| `/weather` | Current weather |
| `sleep` / `goodnight` | Enter sleep mode |
| `wake` / `good morning` | Exit sleep mode |

## Scheduled Alerts

Configured in `user_profile.json` → `telegram`:

| Time | Alert | Config Key |
|------|-------|-----------|
| 8:00 AM | Morning brief (weather, tasks, goals) | `morning_brief: true` |
| 8:00 PM (default) | Evening check-in (completed, pending, streak) | `goal_checkin_time: "20:00"` |
