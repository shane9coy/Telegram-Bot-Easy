---
name: telegram
description: Telegram Bot Agent - Control the always-listening Telegram daemon, send messages, manage tasks/goals, and configure notifications.
---

# Telegram Agent

Control the Telegram always-listening daemon and send/receive messages.

## Listener Control

| Command | What It Does |
|---------|-------------|
| `/telegram start` | Start listener in background (`python telegram_listener.py --daemon`) |
| `/telegram stop` | Stop the running listener (`python telegram_listener.py --stop`) |
| `/telegram status` | Check if listener is running, mode (listening/sleeping), PID |
| `/telegram sleep` | Put listener to sleep (only scheduled alerts, no command responses) |
| `/telegram wake` | Wake listener up (resume command responses) |
| `/telegram restart` | Stop then start the listener |
| `/telegram logs` | Show recent listener logs (`tail logs/telegram_listener.log`) |

## Send Messages

| Command | What It Does |
|---------|-------------|
| `/telegram send "message"` | Send a message to the user via Telegram |
| `/telegram brief` | Send the morning briefing now (weather, tasks, goals) |
| `/telegram alert "message"` | Send a system alert notification |

## Bot Commands (via Telegram)

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

## Building Custom Commands

Use the `telegram-builder` skill for detailed guidance on adding new integrations.

### Quick Pattern

1. Add helper in `telegram_helpers.py`
2. Import in `telegram_listener.py`
3. Add handler in `route_command()`

See `templates/helper_template.py` for complete examples.

## Scheduled Alerts

Configured in `user_profile.json` → `telegram`:

| Time | Alert | Config Key |
|------|-------|-----------|
| 8:00 AM | Morning brief (weather, tasks, goals) | `morning_brief: true` |
| 8:00 PM (default) | Evening check-in (completed, pending, streak) | `goal_checkin_time: "20:00"` |

## Configuration

Edit `.claude/user_profile.json` → `telegram` section:

```json
{
  "telegram": {
    "chat_id": null,
    "notifications_enabled": true,
    "morning_brief": true,
    "task_reminders": true,
    "goal_checkin_time": "20:00",
    "always_listening": true
  }
}
```

## Architecture

Two-tier approach — daemon is standalone Python:

| Tier | How | Commands |
|------|-----|---------|
| **Direct** | Pure Python (API calls, file reads) | weather, tasks, goals, status |
| **Queue** | Write to `/tmp/telegram_agent_queue.json` | complex queries |

## Implementation

- **Scripts:** `telegram_listener.py` + `telegram_helpers.py` (project root)
- **Session:** `~/mcp-servers/telegram-mcp/telegram_bot.session`
- **Logs:** `logs/telegram_listener.log`
- **PID:** `/tmp/telegram_listener.pid`
- **State:** `/tmp/telegram_listener_state.json`
- **Agent queue:** `/tmp/telegram_agent_queue.json`

## Running as a Service (launchd)

```bash
# Start on login
python telegram_listener.py --daemon

# Or create a launchd plist for auto-start
```

To auto-start on boot, create `~/Library/LaunchAgents/com.yourname.telegram-listener.plist`.
