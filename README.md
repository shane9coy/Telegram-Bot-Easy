# Telegram Bot Easy

A powerful Telegram bot with an always-listening daemon, task/goal management, newsletter integration, astrology features, and more.

## Features

- **Always-Listening Daemon** - Run Telegram listener in the background for 24/7 availability
- **Task & Goal Management** - Create, track, and complete tasks and goals directly from Telegram
- **Daily Habits** - Track recurring daily habits with streaks
- **Project Management** - Organize tasks into projects
- **Newsletter Integration** - Generate and send newsletters via Pulse
- **Oracle Astrology** - Daily horoscopes, moon phases, weekly outlooks
- **Vibe Curations** - Daily recommendations for food, music, outfits, and activities
- **Human Task Delegation** - Post bounties and hire humans via RentAHuman.ai
- **Scheduled Alerts** - Morning briefings and evening check-ins
- **Sleep/Wake Modes** - Control when the bot responds to commands

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
# Run in foreground
python telegram_listener.py

# Run as background daemon
python telegram_listener.py --daemon
```

See telegram_guide.md for full documentation.

## License

MIT License - see LICENSE file for details.
