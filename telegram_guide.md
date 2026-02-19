# Telegram Bot Guide — Katana Agent

Complete guide for the Telegram integration: always-listening bot daemon, command reference, server management, and troubleshooting.

---

## Quick Reference — Server Management

### Start / Stop / Status

```bash
# Check if listener is running
python3 telegram_listener.py --status

# Start in foreground (see logs live)
python3 telegram_listener.py

# Start as background daemon
python3 telegram_listener.py --daemon

# Stop the running listener
python3 telegram_listener.py --stop

# Enter sleep mode (no responses, only scheduled alerts)
python3 telegram_listener.py --sleep

# Wake from sleep mode
python3 telegram_listener.py --wake
```

### After Updating `.env` Variables

The listener loads environment variables at startup. If you add or change a key in `.env`, **you must restart**:

```bash
cd ~/News\ Letter
python3 telegram_listener.py --stop
python3 telegram_listener.py --daemon
```

Common variables that require a restart when changed:

| Variable | File | Used By |
|----------|------|---------|
| `RENTAHUMAN_API_KEY` | `.env` | `/rent` commands |
| `SUPABASE_URL` / `SUPABASE_KEY` | `.env` | `/pulse stats`, subscriber queries |
| `KATANA_HTTP_TELEGRAM_BOT_TOKEN` | `.env` | Bot authentication |
| `TELEGRAM_BOT_USER_ID` | `.env` | Message filtering (only responds to this user) |
| `TELEGRAM_API_ID` / `TELEGRAM_API_HASH` | `~/mcp-servers/telegram-mcp/.env` | Telethon client auth |

### After Updating Code

If you edit `telegram_listener.py` or `telegram_helpers.py`, restart the daemon to pick up changes:

```bash
python3 telegram_listener.py --stop && python3 telegram_listener.py --daemon
```

### Logs

```bash
# Live tail of listener logs
tail -f ~/News\ Letter/logs/telegram_listener.log

# Check recent activity
tail -50 ~/News\ Letter/logs/telegram_listener.log
```

### Run as macOS Launch Agent (always-on)

Create `~/Library/LaunchAgents/com.katana.telegram-listener.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.katana.telegram-listener</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/Users/sc/News Letter/telegram_listener.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>WorkingDirectory</key>
    <string>/Users/sc/News Letter</string>
    <key>StandardOutPath</key>
    <string>/Users/sc/News Letter/logs/telegram_listener.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/sc/News Letter/logs/telegram_listener_error.log</string>
</dict>
</plist>
```

```bash
# Load (start at login)
launchctl load ~/Library/LaunchAgents/com.katana.telegram-listener.plist

# Unload (stop)
launchctl unload ~/Library/LaunchAgents/com.katana.telegram-listener.plist

# Check status
launchctl list | grep katana
```

### PID & State Files

| File | Purpose |
|------|---------|
| `/tmp/telegram_listener.pid` | Running process ID |
| `/tmp/telegram_listener_state.json` | Sleep/wake state |
| `/tmp/telegram_agent_queue.json` | Queued commands for Claude agent pickup |

---

## Architecture

```
┌──────────────────┐          ┌────────────────────────┐
│  Telegram User   │◀────────▶│  telegram_listener.py  │
│  (phone/desktop) │  Telethon│  (Katana Bot daemon)   │
└──────────────────┘  Bot API │                        │
                              │  route_command()        │
                              │    ├─ handle_oracle()   │
                              │    ├─ handle_pulse()    │
                              │    ├─ handle_vibe()     │
                              │    ├─ handle_rent()     │
                              │    ├─ handle_weather()  │
                              │    ├─ handle_*_task()   │
                              │    └─ ...               │
                              └──────────┬─────────────┘
                                         │ imports
                              ┌──────────▼─────────────┐
                              │  telegram_helpers.py    │
                              │  (pure Python engine)   │
                              │                         │
                              │  Oracle: moon, signs,   │
                              │    horoscope, events    │
                              │  Pulse: news, stats     │
                              │  Vibe: food, music,     │
                              │    outfit, activity     │
                              │  Rent: bounties, skills │
                              └──────────┬─────────────┘
                                         │ HTTP
                              ┌──────────▼─────────────┐
                              │  External APIs          │
                              │  • Supabase (DB)        │
                              │  • Open-Meteo (weather) │
                              │  • RentAHuman (tasks)   │
                              └─────────────────────────┘
```

### Key Files

| File | Purpose |
|------|---------|
| `telegram_listener.py` | Bot daemon — Telethon client, event handler, command router, scheduled alerts |
| `telegram_helpers.py` | Pure-Python helpers — no MCP or Claude deps, only stdlib + requests + supabase |
| `.env` | API keys (Supabase, RentAHuman, Telegram creds, Mailgun, etc.) |
| `~/mcp-servers/telegram-mcp/.env` | Telegram API credentials (API_ID, API_HASH, USER_ID) |
| `.claude/user_profile.json` | User profile (birth chart, preferences, daily tracker, telegram config) |

### Two Telegram Integrations

This project has **two separate** Telegram integrations:

1. **Katana Bot** (`telegram_listener.py`) — A Telegram **bot** (uses bot token). Runs as a daemon, listens for commands from the user, responds automatically. This is the always-listening system.

2. **Telegram MCP Server** (`~/mcp-servers/telegram-mcp/`) — A **userbot** (uses API_ID/API_HASH with session). Provides 60+ tools to Claude/OpenCode for sending messages, managing chats, etc. Used by the Master Agent for push notifications.

They share the same Telegram API credentials but use different session files and serve different purposes.

---

## Available Commands

Send these to @KatanaAgent_bot (or whatever your bot is named).

### System

| Command | Description |
|---------|-------------|
| `/help` | Full command list |
| `/status` | Listener mode, pending tasks, PID |
| `/weather` | Current weather (from Open-Meteo) |
| `sleep` / `goodnight` | Enter sleep mode (only scheduled alerts) |
| `wake` / `good morning` | Exit sleep mode |

### Oracle (Astrology)

| Command | Description |
|---------|-------------|
| `/oracle` | Today's full horoscope (sun + moon + rising readings) |
| `/oracle moon` | Current moon phase + energy |
| `/oracle week` | 7-day outlook (moon phases + day energy) |
| `/oracle vibe` | Planetary vibe (dominant sign + day ruler) |

### Pulse (Newsletter)

| Command | Description |
|---------|-------------|
| `/pulse` | Pipeline status (ranked news + email files) |
| `/pulse news` | Top headlines (auto-pulls feeds if none exist) |
| `/pulse stats` | Subscriber count from Supabase |
| `/pulse newsletter` | Read today's newsletter text |
| `/pulse newsletter gen` | Generate newsletter (runs full pipeline) |
| `/pulse send` | Send newsletter to subscribers |

### Vibe (Daily Recommendations)

| Command | Description |
|---------|-------------|
| `/vibe` | Full daily vibe (weather + oracle + food + music + activity + outfit) |
| `/vibe food` | Food recommendation from preferences |
| `/vibe music` | Music/genre recommendation |
| `/vibe outfit` | What to wear (temperature-based) |
| `/vibe activity` | Activity pick from preferences |

### Rent (Human Task Delegation)

| Command | Description |
|---------|-------------|
| `/rent` | List active bounties |
| `/rent jobs` | List active bounties |
| `/rent skills` | Available skills on RentAHuman |
| `/rent post <desc>` | Create a new bounty (first sentence = title) |

### Tasks & Goals

| Command | Description |
|---------|-------------|
| `/tasks` | Today's pending tasks |
| `add task: <text>` | Add a new task |
| `done: <text>` or `done <#>` | Complete a task by name or number |
| `/goals` | Active goals |
| `add goal: <text>` | Add a new goal |
| `/progress` | Today's stats (pending, completed, streak) |

### Projects

| Command | Description |
|---------|-------------|
| `/projects` | List all projects with task counts |
| `/project <name>` | Show tasks for a specific project |
| `add project: <name>` | Create a new project |
| `add to <project>: <task>` | Add a task to a project |

### Habits

| Command | Description |
|---------|-------------|
| `/habits` | List daily habits with streaks |
| `add habit: <text>` | Add a new daily habit |
| `habit done: <text>` or `habit done <#>` | Mark habit complete for today |

### Agent Queue

| Command | Description |
|---------|-------------|
| `order <what>` | Queue an order for Claude agent pickup |
| `book <what>` | Queue a booking for Claude agent pickup |

These commands require web interaction (Playwright) and are queued to `/tmp/telegram_agent_queue.json` for the terminal agent to process.

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

### `user_profile.json` → `telegram` section

```json
{
  "telegram": {
    "chat_id": 6812925961,
    "notifications_enabled": true,
    "morning_brief": true,
    "task_reminders": true,
    "goal_checkin_time": "20:00",
    "always_listening": true
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

**`~/mcp-servers/telegram-mcp/.env`:**
```env
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=your_api_hash
TELEGRAM_SESSION_NAME=katana_bot
TELEGRAM_BOT_USER_ID=your_user_id
```

**`~/News Letter/.env`:**
```env
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=your_api_hash
TELEGRAM_BOT_USER_ID=your_user_id
KATANA_HTTP_TELEGRAM_BOT_TOKEN=your_bot_token
```

### Step 5: Authenticate

```bash
cd ~/News\ Letter
python3 telegram_listener.py
```

First run prompts for phone number verification (one-time). After that, the bot token handles auth.

### Step 6: Verify

Send `/help` to your bot in Telegram. You should get the command list back.

---

## Telegram MCP Tools (for Claude/OpenCode)

These are available when the `telegram-mcp` server is running in Claude/OpenCode (separate from the listener daemon):

### Core Tools

| Tool | Purpose |
|------|---------|
| `telegram_send_message` | Send text to any chat (chat_id + text) |
| `telegram_get_messages` | Read messages from a chat |
| `telegram_get_me` | Verify connection / get user info |
| `telegram_send_photo` | Send images (charts, screenshots) |
| `telegram_send_document` | Send files (newsletter HTML, reports) |
| `telegram_get_dialogs` | List all chats/channels |

### Usage from Master Agent

The Master Agent uses these tools (not the listener) for:
- Pushing morning briefings
- Sending alerts (newsletter published, system health)
- Responding to queued commands
- Two-way conversation when at the terminal

```
# Example: Send a message from Claude
Use telegram_send_message with chat_id 6812925961 and text "Newsletter sent successfully"
```

---

## Troubleshooting

### "RentAHuman API key not configured" (or any missing env var)

**Cause:** Listener was started before the variable was added to `.env`.
**Fix:** Restart the daemon:
```bash
python3 telegram_listener.py --stop && python3 telegram_listener.py --daemon
```

### Bot not responding to messages

1. Check it's running: `python3 telegram_listener.py --status`
2. Check it's not sleeping: look at status output for "mode: sleeping"
3. Verify `TELEGRAM_BOT_USER_ID` matches your actual Telegram user ID
4. Check logs: `tail -20 ~/News\ Letter/logs/telegram_listener.log`

### Session expired / AUTH_KEY_UNREGISTERED

```bash
# Delete bot session file and re-authenticate
rm ~/mcp-servers/telegram-mcp/katana_bot.session*
python3 telegram_listener.py
```

### Markdown parse errors in replies

The listener tries markdown first, falls back to plain text on failure (see `telegram_listener.py:764-767`). If responses look broken, the source helper function likely has unescaped markdown characters.

### Messages sent but not received on phone

1. Check Telegram app notifications are enabled
2. Verify `chat_id` in `user_profile.json` is correct
3. Check Do Not Disturb / Focus mode on your phone
4. Make sure the bot isn't muted in Telegram

### "Listener not running (stale PID file)"

The process crashed but left its PID file. Just start it again:
```bash
python3 telegram_listener.py --daemon
```

### Two listeners running simultaneously

```bash
python3 telegram_listener.py --stop    # Stops by PID
ps aux | grep telegram_listener        # Check for stragglers
kill <pid>                             # Kill any remaining
python3 telegram_listener.py --daemon  # Fresh start
```

---

## Adding New Commands

To add a new command to the bot:

### 1. Add the helper function to `telegram_helpers.py`

```python
def get_my_new_thing():
    """Pure Python — no MCP, no Claude, just logic."""
    return "Result here"
```

### 2. Add the handler to `telegram_listener.py`

```python
def handle_my_command(lower):
    if lower == "mycommand":
        return get_my_new_thing()
    return "Default response"
```

### 3. Add routing in `route_command()`

```python
if lower.startswith("mycommand"):
    return handle_my_command(lower)
```

### 4. Add to the help text

Update the help string in `route_command()` (around line 626).

### 5. Restart the daemon

```bash
python3 telegram_listener.py --stop && python3 telegram_listener.py --daemon
```

---

## Security

- **Never commit `.env` files** — they contain API keys and credentials
- **Protect session files**: `chmod 600 ~/mcp-servers/telegram-mcp/*.session*`
- **Bot only responds to `USER_ID`** — other users are silently ignored (`telegram_listener.py:755`)
- **Enable 2FA** on your Telegram account
- **Rotate bot token** if compromised: BotFather → `/revoke` → update `.env` → restart
