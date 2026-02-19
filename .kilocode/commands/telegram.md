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

The user can send these commands directly to @KatanaAgent_bot:

### Pulse (Newsletter)
| Command | Action |
|---------|--------|
| `/pulse` | Pipeline status |
| `/pulse newsletter` | Send today's NL to you via Telegram |
| `/pulse newsletter gen` | Generate today's newsletter |
| `/pulse stats` | Subscriber count |
| `/pulse send` | Trigger email send to subscribers |
| `/pulse news` | Top headlines from ranked_news |

### Oracle (Astrology)
| Command | Action |
|---------|--------|
| `/oracle` | Daily horoscope (sun/moon/rising) |
| `/oracle week` | Week ahead outlook |
| `/oracle moon` | Current moon phase & energy |
| `/oracle vibe` | Planetary vibe (moon + day energy) |

### Vibe (Daily Recs)
| Command | Action |
|---------|--------|
| `/vibe` | Full vibe (weather + oracle + food + music + activity) |
| `/vibe food` | Food recommendation |
| `/vibe music` | Music recommendation |
| `/vibe outfit` | What to wear |
| `/vibe activity` | What to do today |
| `/vibe activity <query>` | Activities for date/location (queued for agent) |

### Calendar
| Command | Action |
|---------|--------|
| `/calendar` | Today's events (Phase 2 — requires terminal agent) |

### Rent (Human Tasks)
| Command | Action |
|---------|--------|
| `/rent` | Active bounties summary |
| `/rent jobs` | List open bounties |
| `/rent post <desc>` | Post a new bounty |
| `/rent skills` | List available skills |

### Tasks & Goals
| Command | Action |
|---------|--------|
| `/tasks` | Today's tasks |
| `add task: ...` | Add a task |
| `done: ...` / `done 1` | Complete a task |
| `/goals` | Active goals |
| `add goal: ...` | Add a goal |
| `/progress` | Today's stats + streak |

### Projects
| Command | Action |
|---------|--------|
| `/projects` | List projects |
| `/project <name>` | Show project tasks |
| `add project: <name>` | Create a project |
| `add to <project>: <task>` | Add task to a project |

### Habits
| Command | Action |
|---------|--------|
| `/habits` | Daily habits + streaks |
| `add habit: ...` | Add recurring daily habit |
| `habit done: ...` | Mark habit complete for today |

### Agent Queue
| Command | Action |
|---------|--------|
| `/order <what>` | Order food (queued for agent) |
| `/book <what>` | Book reservation (queued for agent) |

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

Two-tier approach — daemon is standalone Python, can't call Claude MCP:

| Tier | How | Commands |
|------|-----|---------|
| **Direct** | Pure Python (API calls, file reads, Supabase, profile data) | stats, weather, tasks, goals, habits, projects, pulse status/news, oracle, vibe, rent |
| **Subprocess** | Shell out to `send_newsletter.py`, `agent_orchestrator.py` | pulse send, pulse newsletter gen |
| **Queue** | Write to `/tmp/telegram_agent_queue.json` for Claude pickup | order, book, vibe activity <query> |

## Implementation

- **Scripts:** `telegram_listener.py` + `telegram_helpers.py` (project root)
- **Session:** Reuses `~/mcp-servers/telegram-mcp/katana_bot.session`
- **Logs:** `logs/telegram_listener.log`
- **PID:** `/tmp/telegram_listener.pid`
- **State:** `/tmp/telegram_listener_state.json`
- **Agent queue:** `/tmp/telegram_agent_queue.json`

## Running as a Service (launchd)

```bash
# Start on login
python telegram_listener.py --daemon

# Or create a launchd plist for auto-start (see below)
```

To auto-start on boot, create `~/Library/LaunchAgents/com.magi3.telegram-listener.plist`.
