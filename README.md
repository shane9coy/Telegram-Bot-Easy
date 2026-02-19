# Telegram Bot Easy 🤖
Designed for your CLI agent editor to take the reigns. Build your own custom Telegram bot with minimal setup. A powerful, extensible Telegram bot template with an always-listening daemon, task/goal management, and preconfigured .agent folders with SKILLs and resources for building out your own custom bots.

<img width="900" height="762" alt="image (9) (5)" src="https://github.com/user-attachments/assets/2fdd41e7-45db-494e-bf73-a5475f8459e8" />

## ✨ Key Features

- **🤖 Always-Listening Daemon** - Run 24/7 in the background, responding to commands instantly
- **📋 Task & Goal Management** - Create, track, and complete tasks and goals from Telegram
- **🔥 Daily Streaks** - Track productivity with streak counters
- **⏰ Scheduled Alerts** - Morning briefings and evening check-ins
- **😴 Sleep/Wake Modes** - Control when the bot responds
- **🛠️ Extensible Template** - Easy to add your own integrations and APIs
- **🤝 Agent Skill Integration** - Works with Claude, Cursor, and other AI assistants

## 🚀 Quick Start

### Prerequisites

1. **Python 3.8+** installed
2. **Telegram account** for bot creation

### Step 1: Get Telegram Credentials

| Credential | How to Get |
|------------|------------|
| `TELEGRAM_BOT_TOKEN` | Message [@BotFather](https://t.me/BotFather) → `/newbot` |
| `TELEGRAM_BOT_USER_ID` | Message [@userinfobot](https://t.me/userinfobot) |
| `TELEGRAM_API_ID` | Go to [my.telegram.org](https://my.telegram.org) → API Development Tools |
| `TELEGRAM_API_HASH` | Go to [my.telegram.org](https://my.telegram.org) → API Development Tools |

### Step 2: Install & Configure

```bash
# Clone the repo
git clone https://github.com/shane9coy/telegram-bot-easy.git
cd telegram-bot-easy

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env
# Edit .env with your credentials

# Create logs directory
mkdir -p logs
```

### Step 3: Run the Bot

```bash
# Start as background daemon
python telegram_listener.py --daemon

# Verify it's running
python telegram_listener.py --status
```

### Step 4: Test

Send `/help` to your bot on Telegram!

---

## 📁 Project Structure

```
Telegram/
├── telegram_listener.py      # Core daemon (handles messages, routing)
├── telegram_helpers.py       # Helper functions (add your services here)
├── templates/
│   └── helper_template.py    # Full integration pattern reference
├── .kilocode/skills/
│   ├── telegram/SKILL.md     # Main skill (usage + setup)
│   └── telegram-builder/SKILL.md  # Builder skill (dev guide)
├── .claude/skills/
│   └── telegram/SKILL.md     # Synced with .kilocode version
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🎮 Bot Commands

### System
| Command | Description |
|---------|-------------|
| `/help` | Full command list |
| `/status` | Listener mode, pending tasks, PID |
| `/weather` | Current weather |
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

---

## 🛠️ Building New Integrations

This template is designed to be extended. Add your own services easily:

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

See [`templates/helper_template.py`](templates/helper_template.py) for a complete integration example with:
- API client pattern
- Error handling
- Response formatting
- User profile integration

### Agent Skills

The `telegram-builder` skill provides detailed guidance for AI assistants to help you build integrations.

---

## 📋 CLI Commands

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

# View logs
tail -f logs/telegram_listener.log
```

---

## ⚙️ Configuration

### Environment Variables (`.env`)

```env
# Required
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_BOT_USER_ID=123456789
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=your_api_hash_here

# Optional - add your own API keys
# MY_API_KEY=your_key_here
```

### User Profile (`user_profile.json`)

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

---

## 🔧 Troubleshooting

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

### After Updating Code

```bash
python telegram_listener.py --stop && python telegram_listener.py --daemon
```

---

## 🤝 For AI Assistants

If you're an AI assistant (Claude, Cursor, etc.) helping set up this bot:

### Setup Checklist

- [ ] Verify Python 3.8+ is installed
- [ ] Run `pip install -r requirements.txt`
- [ ] Copy `.env.example` to `.env`
- [ ] Guide user to get Telegram credentials
- [ ] Create logs directory: `mkdir -p logs`
- [ ] Start daemon: `python telegram_listener.py --daemon`
- [ ] Verify: `python telegram_listener.py --status`
- [ ] Test: Send `/help` to the bot

### Skills Available

- **telegram** - Main skill for bot usage and setup
- **telegram-builder** - Guide for building new integrations

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 🙏 Credits

Built by [@shaneswrld_](https://x.com/shaneswrld_) | [GitHub](https://github.com/shane9coy)

---

## 🔗 Related Resources

- [Telegram Bot API Docs](https://core.telegram.org/bots/api)
- [Telethon Documentation](https://docs.telethon.dev/)
- [Agent Skill Architecture Guide](https://github.com/shane9coy/Agent-Skill-Architecture-Guide)
