---
name: telegram
triggers: "send telegram, telegram message, telegram listener, start daemon, stop daemon, telegram notification, push notification, telegram bot, @KatanaAgent_bot, telegram alert"
description: "Control the always-listening Telegram daemon, send messages, manage the task/goal bot, and configure scheduled alerts."
---

# Telegram Skill

Auto-activate for Telegram message sending, daemon control, or bot configuration.

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
/telegram send "Your message here"
/telegram brief          # Send morning briefing now
/telegram alert "msg"    # System alert notification
```

## Architecture

Two-tier — daemon is standalone Python, cannot call Claude MCP directly:

| Tier | Mechanism | Commands |
|------|-----------|---------|
| **Direct** | Pure Python + Supabase + API calls | tasks, goals, habits, weather, oracle vibe, pulse status |
| **Subprocess** | Shell to `agent_orchestrator.py` | pulse send, newsletter gen |
| **Queue** | Write to `/tmp/telegram_agent_queue.json` | order, book, vibe activity queries |

## Key Files

- Script: `telegram_listener.py` + `telegram_helpers.py`
- Session: `~/mcp-servers/telegram-mcp/katana_bot.session`
- PID: `/tmp/telegram_listener.pid`
- State: `/tmp/telegram_listener_state.json`
- Logs: `logs/telegram_listener.log`
- Queue: `/tmp/telegram_agent_queue.json`

## Config (user_profile.json → telegram)

```json
{ "chat_id": null, "notifications_enabled": true, "morning_brief": true,
  "task_reminders": true, "goal_checkin_time": "20:00", "always_listening": true }
```

→ Full bot command reference: `.claude/commands/telegram.md`
