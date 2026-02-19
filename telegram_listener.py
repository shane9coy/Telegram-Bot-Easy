#!/usr/bin/env python3
"""
Telegram Always-Listening Daemon - Base Template

Connects to Telegram via Telethon, listens for messages from the user,
routes commands, manages daily tasks/goals, and sends scheduled alerts.

Usage:
    python telegram_listener.py                  # Run in foreground
    python telegram_listener.py --daemon         # Run as background daemon
    python telegram_listener.py --sleep          # Enter sleep mode (no responses, only scheduled alerts)
    python telegram_listener.py --wake           # Exit sleep mode
    python telegram_listener.py --status         # Check listener status
    python telegram_listener.py --stop           # Stop the running listener

Control via Telegram:
    sleep / goodnight       → Enter sleep mode
    wake / good morning     → Exit sleep mode
    status                  → Check listener status

Built by: x.com/@shaneswrld_ | github.com/shane9coy
"""

import os
import sys
import json
import signal
import asyncio
import logging
from datetime import datetime, date
from pathlib import Path

from dotenv import load_dotenv
from telethon import TelegramClient, events

# Import helpers - add your custom imports here
from telegram_helpers import get_status, get_weather_example, get_help

# ── Config ──────────────────────────────────────────────────
TELEGRAM_MCP_DIR = Path.home() / "mcp-servers" / "telegram-mcp"
PROJECT_DIR = Path(__file__).parent
PROFILE_PATH = PROJECT_DIR / ".claude" / "user_profile.json"
PID_FILE = Path("/tmp/telegram_listener.pid")
STATE_FILE = Path("/tmp/telegram_listener_state.json")

load_dotenv(TELEGRAM_MCP_DIR / ".env")  # API_ID, API_HASH, USER_ID live here
load_dotenv(PROJECT_DIR / ".env")  # Bot token lives here (won't override existing keys)

API_ID = int(os.getenv("TELEGRAM_API_ID", "0"))
API_HASH = os.getenv("TELEGRAM_API_HASH", "")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
SESSION_NAME = "telegram_bot"  # Bot session — separate from userbot MCP server
USER_ID = int(os.getenv("TELEGRAM_BOT_USER_ID", "0"))

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(PROJECT_DIR / "logs" / "telegram_listener.log"),
    ],
)
log = logging.getLogger("telegram_listener")

# ── Profile helpers ─────────────────────────────────────────


def load_profile():
    try:
        return json.loads(PROFILE_PATH.read_text())
    except Exception:
        return {}


def save_profile(profile):
    PROFILE_PATH.write_text(json.dumps(profile, indent=2))


def get_tracker(profile):
    tracker = profile.setdefault("daily_tracker", {})
    today = date.today().isoformat()
    if tracker.get("today") != today:
        # New day — archive yesterday, reset
        if tracker.get("tasks"):
            tracker.setdefault("history", []).append(
                {
                    "date": tracker.get("today"),
                    "tasks": tracker.get("tasks", []),
                    "completed": tracker.get("completed_today", []),
                }
            )
        tracker["today"] = today
        tracker["tasks"] = []
        tracker["completed_today"] = []
        # Auto-add habits as daily tasks
        for habit in tracker.get("habits", []):
            tracker["tasks"].append(
                {
                    "text": f"✨ {habit['text']}",
                    "added": datetime.now().isoformat(),
                    "status": "pending",
                    "habit": True,
                }
            )
    # Ensure projects and habits exist
    tracker.setdefault("projects", {})
    tracker.setdefault("habits", [])
    return tracker


# ── State management (sleep/wake, pid) ─────────────────────


def load_state():
    try:
        return json.loads(STATE_FILE.read_text())
    except Exception:
        return {"sleeping": False, "sleep_until": None}


def save_state(state):
    STATE_FILE.write_text(json.dumps(state))


def write_pid():
    PID_FILE.write_text(str(os.getpid()))


def read_pid():
    try:
        return int(PID_FILE.read_text().strip())
    except Exception:
        return None


def clear_pid():
    PID_FILE.unlink(missing_ok=True)


# ── Task/Goal commands ──────────────────────────────────────


def handle_add_task(text):
    """Add a task. Input: 'add task: Deploy v2'"""
    task_text = (
        text.split(":", 1)[1].strip()
        if ":" in text
        else text.replace("add task", "").strip()
    )
    if not task_text:
        return "Usage: `add task: Your task here`"
    profile = load_profile()
    tracker = get_tracker(profile)
    tracker["tasks"].append(
        {
            "text": task_text,
            "added": datetime.now().isoformat(),
            "status": "pending",
        }
    )
    save_profile(profile)
    return f"✅ Added: {task_text}"


def handle_done_task(text):
    """Complete a task. Input: 'done: Deploy v2' or 'done 1'"""
    query = (
        text.split(":", 1)[1].strip()
        if ":" in text
        else text.replace("done", "").strip()
    )
    profile = load_profile()
    tracker = get_tracker(profile)
    tasks = tracker.get("tasks", [])

    # Try by number
    try:
        idx = int(query) - 1
        if 0 <= idx < len(tasks):
            task = tasks.pop(idx)
            task["status"] = "completed"
            task["completed_at"] = datetime.now().isoformat()
            tracker.setdefault("completed_today", []).append(task)
            save_profile(profile)
            return f"✅ Completed: {task['text']}"
    except ValueError:
        pass

    # Try by name match
    for i, task in enumerate(tasks):
        if query.lower() in task["text"].lower():
            task = tasks.pop(i)
            task["status"] = "completed"
            task["completed_at"] = datetime.now().isoformat()
            tracker.setdefault("completed_today", []).append(task)
            save_profile(profile)
            return f"✅ Completed: {task['text']}"

    return f"❌ Task not found: {query}"


def handle_list_tasks():
    profile = load_profile()
    tracker = get_tracker(profile)
    tasks = tracker.get("tasks", [])
    if not tasks:
        return "No pending tasks for today."
    lines = ["**Today's Tasks:**", ""]
    for i, t in enumerate(tasks, 1):
        lines.append(f"{i}. {t['text']}")
    done = tracker.get("completed_today", [])
    if done:
        lines.append(f"\n✅ Completed today: {len(done)}")
    return "\n".join(lines)


def handle_add_goal(text):
    query = (
        text.split(":", 1)[1].strip()
        if ":" in text
        else text.replace("add goal", "").strip()
    )
    if not query:
        return "Usage: `add goal: Your goal here`"
    profile = load_profile()
    tracker = get_tracker(profile)
    tracker.setdefault("goals", []).append(
        {
            "text": query,
            "added": datetime.now().isoformat(),
            "status": "active",
        }
    )
    save_profile(profile)
    return f"🎯 Goal added: {query}"


def handle_list_goals():
    profile = load_profile()
    tracker = get_tracker(profile)
    goals = tracker.get("goals", [])
    if not goals:
        return "No active goals."
    lines = ["**Active Goals:**", ""]
    for i, g in enumerate(goals, 1):
        lines.append(f"{i}. {g['text']}")
    return "\n".join(lines)


def handle_progress():
    profile = load_profile()
    tracker = get_tracker(profile)
    pending = len(tracker.get("tasks", []))
    done = len(tracker.get("completed_today", []))
    streak = tracker.get("streak", 0)
    return f"**Progress:**\n⏳ Pending: {pending}\n✅ Completed today: {done}\n🔥 Streak: {streak} days"


# ═══════════════════════════════════════════════════════════
#  CUSTOM COMMAND HANDLERS
#  Add your custom command handlers here
# ═══════════════════════════════════════════════════════════

# Example:
# def handle_my_service(query=None):
#     """Handle /myservice command."""
#     from telegram_helpers import get_my_service
#     return get_my_service(query)


# ── Command router ──────────────────────────────────────────


def route_command(text):
    """Route a Telegram message to the right handler. Returns response string."""
    lower = text.lower().strip()

    # Strip /command prefix so BotFather menu commands hit existing routes
    if lower.startswith("/"):
        lower = lower.lstrip("/").split("@")[0]  # also strip @BotName suffix
        text = (
            text.strip().lstrip("/").split("@")[0]
            if "@" in text
            else text.strip().lstrip("/")
        )

    # /start — BotFather requires this for all bots
    if lower == "start":
        return "🤖 **Telegram Bot is online.**\n\nType /help for commands."

    # Sleep/wake
    if lower in ("sleep", "goodnight", "go to sleep"):
        state = load_state()
        state["sleeping"] = True
        save_state(state)
        return "😴 Going to sleep. I'll only send scheduled alerts. Say 'wake' to resume."

    if lower in ("wake", "good morning", "wake up"):
        state = load_state()
        state["sleeping"] = False
        state["sleep_until"] = None
        save_state(state)
        return "👋 I'm awake! Ready for commands."

    if lower == "status":
        state = load_state()
        mode = "😴 sleeping" if state.get("sleeping") else "👂 listening"
        profile = load_profile()
        tracker = get_tracker(profile)
        pending = len(tracker.get("tasks", []))
        done = len(tracker.get("completed_today", []))
        return f"**Listener Status:** {mode}\n⏳ Tasks pending: {pending}\n✅ Completed today: {done}\n🔢 PID: {os.getpid()}"

    # Check if sleeping (ignore commands except wake/status)
    state = load_state()
    if state.get("sleeping"):
        return None  # Don't respond when sleeping

    # Task commands
    if lower.startswith("add task"):
        return handle_add_task(text)
    if lower.startswith("done"):
        return handle_done_task(text)
    if lower in ("tasks", "task list", "my tasks"):
        return handle_list_tasks()
    if lower.startswith("add goal"):
        return handle_add_goal(text)
    if lower in ("goals", "my goals"):
        return handle_list_goals()
    if lower == "progress":
        return handle_progress()

    # ═══════════════════════════════════════════════════════════
    #  CUSTOM COMMAND ROUTING
    #  Add your custom command routes here
    # ═══════════════════════════════════════════════════════════

    # Example commands using the minimal helpers
    if lower == "weather":
        return get_weather_example()

    # Add your custom commands here:
    # if lower.startswith("/myservice"):
    #     query = text.split(maxsplit=1)[1] if len(text.split()) > 1 else None
    #     return handle_my_service(query)

    if lower in ("help", "commands"):
        return get_help()

    # Fallback — echo that we received it but can't handle it
    return f'📩 Received: "{text}"\n\n(Use /help for available commands)'


# ── Scheduled alerts ────────────────────────────────────────


async def scheduled_alerts(client):
    """Run scheduled alerts (morning brief, evening check-in)."""
    sent_morning = False
    sent_evening = False

    while True:
        now = datetime.now()
        profile = load_profile()
        tg_config = profile.get("telegram", {})

        # Morning brief at 8:00 AM
        if (
            not sent_morning
            and now.hour == 8
            and now.minute == 0
            and tg_config.get("morning_brief", True)
        ):
            weather = get_weather_example()
            tracker = get_tracker(profile)
            tasks = tracker.get("tasks", [])
            goals = tracker.get("goals", [])
            task_list = (
                "\n".join(f"  - {t['text']}" for t in tasks) if tasks else "  None yet"
            )
            goal_list = (
                "\n".join(f"  - {g['text']}" for g in goals) if goals else "  None yet"
            )

            msg = (
                f"**☀️ Good morning!**\n\n"
                f"{weather}\n\n"
                f"**Tasks:**\n{task_list}\n\n"
                f"**Goals:**\n{goal_list}\n\n"
                f"Reply with commands or add tasks!"
            )
            try:
                await client.send_message(USER_ID, msg, parse_mode="md")
                log.info("Morning brief sent")
            except Exception as e:
                log.error(f"Morning brief failed: {e}")
            sent_morning = True

        # Evening check-in
        checkin_time = tg_config.get("goal_checkin_time", "20:00")
        checkin_hour, checkin_min = map(int, checkin_time.split(":"))
        if not sent_evening and now.hour == checkin_hour and now.minute == checkin_min:
            tracker = get_tracker(profile)
            done = tracker.get("completed_today", [])
            pending = tracker.get("tasks", [])
            done_list = (
                "\n".join(f"  - {t['text']}" for t in done) if done else "  Nothing yet"
            )
            pending_list = (
                "\n".join(f"  - {t['text']}" for t in pending)
                if pending
                else "  All done!"
            )

            # Update streak
            if done:
                tracker["streak"] = tracker.get("streak", 0) + 1
            else:
                tracker["streak"] = 0
            save_profile(profile)

            msg = (
                f"**🌙 Evening Check-In**\n\n"
                f"✅ Completed today:\n{done_list}\n\n"
                f"⏳ Still pending:\n{pending_list}\n\n"
                f"🔥 Streak: {tracker.get('streak', 0)} days"
            )
            try:
                await client.send_message(USER_ID, msg, parse_mode="md")
                log.info("Evening check-in sent")
            except Exception as e:
                log.error(f"Evening check-in failed: {e}")
            sent_evening = True

        # Reset flags at midnight
        if now.hour == 0 and now.minute == 0:
            sent_morning = False
            sent_evening = False

        await asyncio.sleep(30)  # Check every 30 seconds


# ── Main listener ───────────────────────────────────────────


async def run_listener():
    session_path = str(TELEGRAM_MCP_DIR / SESSION_NAME)
    client = TelegramClient(session_path, API_ID, API_HASH)

    @client.on(events.NewMessage(from_users=USER_ID))
    async def handler(event):
        text = event.message.text
        if not text:
            return
        log.info(f"Received: {text}")
        response = route_command(text)
        if response:
            try:
                await client.send_message(
                    event.message.peer_id,
                    response,
                    parse_mode="md",
                    reply_to=event.message.id,
                )
            except Exception:
                await client.send_message(
                    event.message.peer_id, response, reply_to=event.message.id
                )
            log.info(f"Replied: {response[:80]}...")

    await client.start(bot_token=BOT_TOKEN)
    me = await client.get_me()
    log.info(f"Telegram bot started as @{me.username} (ID: {me.id})")
    log.info(f"Listening for messages from user ID: {USER_ID}")

    write_pid()
    save_state({"sleeping": False, "sleep_until": None})

    # Send startup notification
    try:
        await client.send_message(
            USER_ID,
            "🤖 **Telegram listener is now active.**\n\nSay 'help' for commands.",
            parse_mode="md",
        )
    except Exception as e:
        log.error(f"Startup notification failed: {e}")

    # Run scheduled alerts in background
    asyncio.create_task(scheduled_alerts(client))

    # Keep running
    await client.run_until_disconnected()


# ── CLI ─────────────────────────────────────────────────────


def main():
    # Ensure logs directory exists
    (PROJECT_DIR / "logs").mkdir(exist_ok=True)

    if len(sys.argv) > 1:
        cmd = sys.argv[1]

        if cmd == "--status":
            pid = read_pid()
            state = load_state()
            if pid:
                # Check if process is running
                try:
                    os.kill(pid, 0)
                    mode = "sleeping" if state.get("sleeping") else "listening"
                    print(f"Listener running (PID {pid}, mode: {mode})")
                except OSError:
                    print("Listener not running (stale PID file)")
                    clear_pid()
            else:
                print("Listener not running")
            return

        if cmd == "--stop":
            pid = read_pid()
            if pid:
                try:
                    os.kill(pid, signal.SIGTERM)
                    print(f"Stopped listener (PID {pid})")
                    clear_pid()
                except OSError:
                    print("Listener not running (stale PID)")
                    clear_pid()
            else:
                print("No listener running")
            return

        if cmd == "--sleep":
            state = load_state()
            state["sleeping"] = True
            save_state(state)
            print("Listener set to sleep mode")
            return

        if cmd == "--wake":
            state = load_state()
            state["sleeping"] = False
            save_state(state)
            print("Listener set to wake mode")
            return

        if cmd == "--daemon":
            # Fork to background
            if os.fork() > 0:
                print(f"Listener started in background")
                return

    # Run the listener
    try:
        asyncio.run(run_listener())
    except KeyboardInterrupt:
        print("\nListener stopped")
        clear_pid()


if __name__ == "__main__":
    main()
