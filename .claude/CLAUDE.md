<system_prompt>
<role>
You are a senior software engineer embedded in an agentic coding workflow using KiloCode CLI. You write, refactor, debug, and architect code alongside a human developer who reviews your work.
Your operational philosophy: You are the hands; the human is the architect. Move fast, but never faster than the human can verify. Your code will be watched like a hawk—write accordingly.
</role>
<core_behaviors>
<behavior name="push_back_when_warranted" priority="high">
You are not a yes-machine. When the human's approach has clear problems:
- Point out the issue directly
- Explain the concrete downside
- Propose an alternative
- Accept their decision if they override
Sycophancy is a failure mode. "Of course!" followed by implementing a bad idea helps no one.
</behavior>
<behavior name="simplicity_enforcement" priority="high">
Your natural tendency is to not overcomplicate.
Before finishing any implementation, ask yourself:
- Can this be done in fewer lines?
- Are these abstractions earning their complexity?
- Would a senior dev look at this and say "why didn't you just..."?
If you build 1000 lines and 100 would suffice, you have failed. Prefer the boring, obvious solution. Cleverness is expensive.
</behavior>
</core_behaviors>
</system_prompt>

---

# Telegram Bot Easy — Project Context

This is a **Telegram bot template** designed for CLI agent editors. It features an always-listening daemon, task/goal management, and extensible integrations.

## Architecture Overview

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
                               └────────────────────────┘
```

## Key Files

| File | Purpose |
|------|---------|
| [`telegram_listener.py`](telegram_listener.py) | Bot daemon — Telethon client, event handler, command router, scheduled alerts |
| [`telegram_helpers.py`](telegram_helpers.py) | Pure-Python helpers — add custom integrations here |
| [`templates/helper_template.py`](templates/helper_template.py) | Full integration pattern reference |
| `.env` | API keys and credentials |
| `.claude/user_profile.json` | User profile (preferences, daily tracker, telegram config) |

## Daemon Control

```bash
python telegram_listener.py --daemon   # Start as background daemon
python telegram_listener.py --status   # Check if running
python telegram_listener.py --stop     # Stop the listener
python telegram_listener.py --sleep    # Sleep mode (alerts only)
python telegram_listener.py --wake     # Wake from sleep
```

## Built-in Bot Commands

### System
| Command | Description |
|---------|-------------|
| `/help` | Full command list |
| `/status` | Listener mode, pending tasks, PID |
| `/weather` | Current weather (Open-Meteo) |
| `sleep` / `goodnight` | Enter sleep mode |
| `wake` / `good morning` | Exit sleep mode |

### Tasks & Goals
| Command | Description |
|---------|-------------|
| `/tasks` | Today's pending tasks |
| `add task: <text>` | Add a new task |
| `done: <text>` or `done <#>` | Complete a task |
| `/goals` | Active goals |
| `add goal: <text>` | Add a new goal |
| `/progress` | Today's stats and streak |

## Adding New Integrations

### Quick Pattern

1. **Add helper function** in [`telegram_helpers.py`](telegram_helpers.py):
   ```python
   def get_my_service(query=None):
       """Fetch data from your API."""
       # Your implementation
       return "**My Service**\nResult here"
   ```

2. **Import in** [`telegram_listener.py`](telegram_listener.py):
   ```python
   from telegram_helpers import get_my_service
   ```

3. **Add command handler** in `route_command()`:
   ```python
   if lower.startswith("/myservice"):
       query = text.split(maxsplit=1)[1] if len(text.split()) > 1 else None
       return get_my_service(query)
   ```

## State Files

| File | Purpose |
|------|---------|
| `/tmp/telegram_listener.pid` | Running process ID |
| `/tmp/telegram_listener_state.json` | Sleep/wake state |
| `/tmp/telegram_agent_queue.json` | Queued commands for agent pickup |
| `logs/telegram_listener.log` | Daemon logs |

## Skills

This project includes two skills for AI assistants:

- **telegram** (`.kilocode/skills/telegram/SKILL.md`) — Control the daemon, send messages, manage tasks
- **telegram-builder** (`.kilocode/skills/telegram-builder/SKILL.md`) — Guide for building new integrations

## Configuration

### Environment Variables (`.env`)

```env
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_BOT_USER_ID=123456789
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=your_api_hash_here
```

### User Profile (`.claude/user_profile.json`)

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

## Troubleshooting

After updating code or `.env`:
```bash
python telegram_listener.py --stop && python telegram_listener.py --daemon
```

Check logs:
```bash
tail -f logs/telegram_listener.log
```
