#!/usr/bin/env python3
"""
Telegram Always-Listening Daemon

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
import subprocess
from datetime import datetime, date, time, timedelta
from pathlib import Path

from dotenv import load_dotenv
from telethon import TelegramClient, events

from telegram_helpers import (
    get_pulse_status, get_top_headlines, get_subscriber_stats, get_newsletter_html,
    get_daily_horoscope, get_moon_phase, get_weekly_outlook, get_oracle_vibe,
    get_simple_vibe, get_vibe_food, get_vibe_music, get_vibe_outfit, get_vibe_activity,
    rent_list_humans, rent_list_bounties, rent_list_skills, rent_create_bounty, rent_status,
)
from bounty_hunter import scan, save_bounty, unsave_bounty, format_saved

# ── Config ──────────────────────────────────────────────────
TELEGRAM_MCP_DIR = Path.home() / "mcp-servers" / "telegram-mcp"
PROJECT_DIR = Path(__file__).parent
PROFILE_PATH = PROJECT_DIR / ".claude" / "user_profile.json"
PID_FILE = Path("/tmp/telegram_listener.pid")
STATE_FILE = Path("/tmp/telegram_listener_state.json")

load_dotenv(TELEGRAM_MCP_DIR / ".env")      # API_ID, API_HASH, USER_ID live here
load_dotenv(PROJECT_DIR / ".env")           # Bot token lives here (won't override existing keys)

API_ID = int(os.getenv("TELEGRAM_API_ID", "0"))
API_HASH = os.getenv("TELEGRAM_API_HASH", "")
BOT_TOKEN = os.getenv("KATANA_HTTP_TELEGRAM_BOT_TOKEN", "")
SESSION_NAME = "katana_bot"  # Bot session — separate from userbot MCP server
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
            tracker.setdefault("history", []).append({
                "date": tracker.get("today"),
                "tasks": tracker.get("tasks", []),
                "completed": tracker.get("completed_today", []),
            })
        tracker["today"] = today
        tracker["tasks"] = []
        tracker["completed_today"] = []
        # Auto-add habits as daily tasks
        for habit in tracker.get("habits", []):
            tracker["tasks"].append({
                "text": f"\u2728 {habit['text']}",
                "added": datetime.now().isoformat(),
                "status": "pending",
                "habit": True,
            })
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
    task_text = text.split(":", 1)[1].strip() if ":" in text else text.replace("add task", "").strip()
    if not task_text:
        return "Usage: `add task: Your task here`"
    profile = load_profile()
    tracker = get_tracker(profile)
    tracker["tasks"].append({
        "text": task_text,
        "added": datetime.now().isoformat(),
        "status": "pending",
    })
    save_profile(profile)
    return f"Added: {task_text}"

def handle_done_task(text):
    """Complete a task. Input: 'done: Deploy v2' or 'done 1'"""
    query = text.split(":", 1)[1].strip() if ":" in text else text.replace("done", "").strip()
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
            return f"Completed: {task['text']}"
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
            return f"Completed: {task['text']}"

    return f"Task not found: {query}"

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
        lines.append(f"\nCompleted today: {len(done)}")
    return "\n".join(lines)

def handle_add_goal(text):
    query = text.split(":", 1)[1].strip() if ":" in text else text.replace("add goal", "").strip()
    if not query:
        return "Usage: `add goal: Your goal here`"
    profile = load_profile()
    tracker = get_tracker(profile)
    tracker.setdefault("goals", []).append({
        "text": query,
        "added": datetime.now().isoformat(),
        "status": "active",
    })
    save_profile(profile)
    return f"Goal added: {query}"

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
    return f"**Progress:**\nPending: {pending}\nCompleted today: {done}\nStreak: {streak} days"

# ── Weather (direct, no MCP needed) ────────────────────────

def handle_weather():
    import requests
    profile = load_profile()
    loc = profile.get("birth_chart", {}).get("location", {})
    lat = loc.get("latitude", 41.4489)
    lon = loc.get("longitude", -82.708)
    name = loc.get("name", "Sandusky, Ohio")
    try:
        r = requests.get("https://api.open-meteo.com/v1/forecast", params={
            "latitude": lat, "longitude": lon,
            "current": "temperature_2m,weather_code,apparent_temperature",
            "temperature_unit": "fahrenheit",
            "timezone": "auto",
        }, timeout=10)
        data = r.json().get("current", {})
        temp = data.get("temperature_2m", "?")
        feels = data.get("apparent_temperature", "?")
        code = data.get("weather_code", 0)
        WMO = {0: "Clear", 1: "Mostly clear", 2: "Partly cloudy", 3: "Overcast",
               45: "Foggy", 51: "Light drizzle", 61: "Rain", 71: "Snow", 80: "Showers", 95: "Thunderstorm"}
        cond = WMO.get(code, "Unknown")
        return f"**Weather — {name}**\n{temp}F (feels {feels}F)\n{cond}"
    except Exception as e:
        return f"Weather error: {e}"

# ── Pulse commands ────────────────────────────────────────

def handle_pulse(lower):
    today = date.today().isoformat()
    if lower in ("pulse", "pulse status"):
        return get_pulse_status(today)
    if lower == "pulse stats":
        return get_subscriber_stats()
    if lower == "pulse news":
        headlines = get_top_headlines(today)
        if "No ranked news found" in headlines:
            # Auto-pull news
            try:
                result = subprocess.run(
                    ["python3", str(PROJECT_DIR / "agent_orchestrator.py"), "--task", "news update"],
                    cwd=str(PROJECT_DIR), capture_output=True, text=True, timeout=120,
                )
                headlines = get_top_headlines(today)
                if "No ranked news found" in headlines:
                    return f"Pulled feeds but no ranked news generated.\n{result.stdout[-300:]}"
            except subprocess.TimeoutExpired:
                return "News pull timed out (2min). Check logs."
            except Exception as e:
                return f"News pull error: {e}"
        return headlines
    if lower == "pulse newsletter":
        html = get_newsletter_html(today)
        if html:
            # Strip HTML tags for Telegram (just send a summary)
            import re
            text = re.sub(r'<[^>]+>', '', html)
            # Truncate for Telegram's 4096 char limit
            if len(text) > 3500:
                text = text[:3500] + "\n\n...(truncated)"
            return f"**Today's Newsletter**\n\n{text}"
        return f"No newsletter found for {today}. Try `/pulse newsletter gen` first."
    if lower == "pulse newsletter gen":
        try:
            # run nl pipeline = full pipeline: pull feeds + rank + generate
            result = subprocess.run(
                ["python3", str(PROJECT_DIR / "agent_orchestrator.py"), "--task", "run nl pipeline"],
                cwd=str(PROJECT_DIR), capture_output=True, text=True, timeout=180,
            )
            output = result.stdout
            if "Newsletter generated" in output or "email_newsletter_final" in output or result.returncode == 0:
                return "Newsletter generated. Check `/pulse` for status."
            # Show stdout (actual errors), not stderr (init noise)
            clean = output.strip() if output.strip() else result.stderr.strip()
            return f"Generation issue:\n{clean[-500:]}"
        except subprocess.TimeoutExpired:
            return "Newsletter generation timed out (3min). Check logs."
        except Exception as e:
            return f"Error: {e}"
    if lower == "pulse send":
        try:
            result = subprocess.run(
                ["python3", str(PROJECT_DIR / "send_newsletter.py")],
                cwd=str(PROJECT_DIR), capture_output=True, text=True, timeout=60,
            )
            if result.returncode == 0:
                return "Newsletter sent to subscribers."
            return f"Send failed:\n{result.stderr[:500]}"
        except Exception as e:
            return f"Error: {e}"
    return get_pulse_status(today)

# ── Oracle commands ───────────────────────────────────────

def handle_oracle(lower):
    profile = load_profile()
    if lower == "oracle":
        return get_daily_horoscope(profile)
    if lower == "oracle moon":
        return get_moon_phase()
    if lower == "oracle week":
        return get_weekly_outlook(profile)
    if lower == "oracle vibe":
        return get_oracle_vibe()
    return get_daily_horoscope(profile)

# ── Vibe commands ─────────────────────────────────────────

def handle_vibe(lower, text):
    profile = load_profile()
    weather_text = handle_weather()
    if lower == "vibe":
        return get_simple_vibe(profile, weather_text)
    if lower == "vibe food":
        return get_vibe_food(profile)
    if lower == "vibe music":
        return get_vibe_music(profile)
    if lower == "vibe outfit":
        return get_vibe_outfit(weather_text)
    if lower == "vibe activity" or lower == "vibe activities":
        return get_vibe_activity(profile)
    if lower.startswith("vibe activity "):
        # Has a query — queue for Claude agent (Phase 2)
        query = text[len("vibe activity "):].strip() if len(text) > len("vibe activity ") else ""
        return handle_agent_queue(f"vibe activity {query}")
    return get_simple_vibe(profile, weather_text)

# ── Calendar commands (stub) ─────────────────────────────

def handle_calendar(lower, text):
    return "Calendar access requires the terminal agent (Google OAuth). Coming in Phase 2.\n\nUse `/calendar` in the Claude terminal for now."

# ── Rent commands ─────────────────────────────────────────

def handle_rent(lower, text):
    if lower == "rent":
        return rent_list_humans()
    if lower == "rent status":
        return rent_status()
    if lower in ("rent bounties", "rent jobs"):
        return rent_list_bounties()
    if lower == "rent skills":
        return rent_list_skills()
    if lower == "rent scan":
        return scan(hours=48, only_new=False, limit=5)
    if lower == "rent scan new":
        return scan(hours=48, only_new=True, limit=5)
    if lower == "rent scan all":
        return scan(hours=9999, only_new=False, limit=10)
    if lower == "rent scan force":
        return scan(hours=48, only_new=False, limit=5, force=True)
    if lower == "rent saved":
        return format_saved()
    if lower.startswith("rent save "):
        bounty_id = text.split("rent save ", 1)[1].strip() if "rent save " in text.lower() else ""
        return save_bounty(bounty_id) if bounty_id else "Usage: `/rent save <bounty_id>`"
    if lower.startswith("rent unsave "):
        bounty_id = text.split("rent unsave ", 1)[1].strip() if "rent unsave " in text.lower() else ""
        return unsave_bounty(bounty_id) if bounty_id else "Usage: `/rent unsave <bounty_id>`"
    if lower.startswith("rent post "):
        desc = text.split("rent post ", 1)[1].strip() if "rent post " in text.lower() else ""
        if not desc:
            return "Usage: `/rent post <description>`"
        parts = desc.split(".", 1)
        title = parts[0].strip()
        body = parts[1].strip() if len(parts) > 1 else title
        return rent_create_bounty(title, body)
    return rent_list_humans()

# ── Project commands ──────────────────────────────────────

def handle_projects(lower, text):
    profile = load_profile()
    tracker = get_tracker(profile)
    projects = tracker.get("projects", {})

    if lower == "projects":
        if not projects:
            return "No projects yet. Use `add project: Name` to create one."
        lines = ["**Projects**", ""]
        for name, proj in projects.items():
            tasks = proj.get("tasks", [])
            pending = sum(1 for t in tasks if t.get("status") == "pending")
            done = sum(1 for t in tasks if t.get("status") == "completed")
            lines.append(f"• **{name}** — {pending} pending, {done} done")
        return "\n".join(lines)

    if lower.startswith("project ") and not lower.startswith("projects"):
        name = text.split(" ", 1)[1].strip() if " " in text else ""
        # Case-insensitive lookup
        match = None
        for k in projects:
            if k.lower() == name.lower():
                match = k
                break
        if not match:
            return f"Project '{name}' not found. Use `/projects` to see all."
        proj = projects[match]
        tasks = proj.get("tasks", [])
        if not tasks:
            return f"**{match}** — No tasks yet. Use `add to {match}: task`"
        lines = [f"**{match}**", ""]
        for i, t in enumerate(tasks, 1):
            status = "done" if t.get("status") == "completed" else "pending"
            lines.append(f"{i}. {t['text']} ({status})")
        return "\n".join(lines)

    if lower.startswith("add project"):
        name = text.split(":", 1)[1].strip() if ":" in text else text.replace("add project", "").strip()
        if not name:
            return "Usage: `add project: Project Name`"
        if name in projects:
            return f"Project '{name}' already exists."
        projects[name] = {"created": date.today().isoformat(), "tasks": []}
        save_profile(profile)
        return f"Project created: {name}"

    if lower.startswith("add to "):
        # "add to Newsletter: Write intro"
        rest = text[len("add to "):].strip()
        if ":" not in rest:
            return "Usage: `add to ProjectName: task description`"
        proj_name, task_text = rest.split(":", 1)
        proj_name = proj_name.strip()
        task_text = task_text.strip()
        if not task_text:
            return "Usage: `add to ProjectName: task description`"
        # Case-insensitive lookup
        match = None
        for k in projects:
            if k.lower() == proj_name.lower():
                match = k
                break
        if not match:
            return f"Project '{proj_name}' not found. Create it first with `add project: {proj_name}`"
        projects[match]["tasks"].append({
            "text": task_text, "status": "pending", "added": datetime.now().isoformat()
        })
        save_profile(profile)
        return f"Added to {match}: {task_text}"

    return handle_projects.__doc__ or "Use `/projects` to list projects."

# ── Habit commands ────────────────────────────────────────

def handle_habits(lower, text):
    profile = load_profile()
    tracker = get_tracker(profile)
    habits = tracker.get("habits", [])
    today = date.today().isoformat()

    if lower == "habits":
        if not habits:
            return "No habits yet. Use `add habit: Read 20min` to start."
        lines = ["**Daily Habits**", ""]
        for i, h in enumerate(habits, 1):
            done_today = today in h.get("completed_dates", [])
            check = "done" if done_today else "pending"
            streak = h.get("streak", 0)
            lines.append(f"{i}. {h['text']} ({check}) — streak: {streak}d")
        return "\n".join(lines)

    if lower.startswith("add habit"):
        habit_text = text.split(":", 1)[1].strip() if ":" in text else text.replace("add habit", "").strip()
        if not habit_text:
            return "Usage: `add habit: Read 20min`"
        habits.append({
            "text": habit_text,
            "added": datetime.now().isoformat(),
            "streak": 0,
            "completed_dates": [],
        })
        save_profile(profile)
        return f"Habit added: {habit_text}"

    if lower.startswith("habit done"):
        query = text.split(":", 1)[1].strip() if ":" in text else text.replace("habit done", "").strip()
        if not query:
            return "Usage: `habit done: Read` or `habit done 1`"
        # Find habit by number or name
        habit = None
        try:
            idx = int(query) - 1
            if 0 <= idx < len(habits):
                habit = habits[idx]
        except ValueError:
            for h in habits:
                if query.lower() in h["text"].lower():
                    habit = h
                    break
        if not habit:
            return f"Habit not found: {query}"
        completed = habit.setdefault("completed_dates", [])
        if today in completed:
            return f"Already completed today: {habit['text']}"
        completed.append(today)
        # Update streak
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        if yesterday in completed:
            habit["streak"] = habit.get("streak", 0) + 1
        else:
            habit["streak"] = 1
        # Also mark corresponding habit task as done
        for task in tracker.get("tasks", []):
            if task.get("habit") and habit["text"] in task["text"]:
                task["status"] = "completed"
                task["completed_at"] = datetime.now().isoformat()
                tracker.setdefault("completed_today", []).append(task)
                tracker["tasks"].remove(task)
                break
        save_profile(profile)
        return f"Habit done: {habit['text']} (streak: {habit['streak']}d)"

    return "Use `/habits` to list, `add habit: ...` to create, `habit done: ...` to complete."

# ── Agent queue (order/book) ─────────────────────────────

AGENT_QUEUE_FILE = Path("/tmp/telegram_agent_queue.json")

def handle_agent_queue(text):
    """Queue a command for Claude agent pickup."""
    try:
        queue = json.loads(AGENT_QUEUE_FILE.read_text()) if AGENT_QUEUE_FILE.exists() else []
    except Exception:
        queue = []
    queue.append({
        "text": text,
        "queued_at": datetime.now().isoformat(),
        "status": "pending",
    })
    AGENT_QUEUE_FILE.write_text(json.dumps(queue, indent=2))
    return "Queued for agent. Will notify when done."

# ── Command router ──────────────────────────────────────────

def route_command(text):
    """Route a Telegram message to the right handler. Returns response string."""
    lower = text.lower().strip()

    # Strip /command prefix so BotFather menu commands hit existing routes
    # e.g. "/help" → "help", "/status" → "status", "/weather" → "weather"
    if lower.startswith("/"):
        lower = lower.lstrip("/").split("@")[0]  # also strip @BotName suffix
        # Also strip from original text so handlers get clean input
        text = text.strip().lstrip("/").split("@")[0] if "@" in text else text.strip().lstrip("/")

    # /start — BotFather requires this for all bots
    if lower == "start":
        return "Katana Agent is online. Type /help for commands."

    # Sleep/wake
    if lower in ("sleep", "goodnight", "go to sleep"):
        state = load_state()
        state["sleeping"] = True
        save_state(state)
        return "Going to sleep. I'll only send scheduled alerts. Say 'wake' to resume."

    if lower in ("wake", "good morning", "wake up"):
        state = load_state()
        state["sleeping"] = False
        state["sleep_until"] = None
        save_state(state)
        return "I'm awake! Ready for commands."

    if lower == "status":
        state = load_state()
        mode = "sleeping" if state.get("sleeping") else "listening"
        profile = load_profile()
        tracker = get_tracker(profile)
        pending = len(tracker.get("tasks", []))
        done = len(tracker.get("completed_today", []))
        return f"**Listener Status:** {mode}\nTasks pending: {pending}\nCompleted today: {done}\nPID: {os.getpid()}"

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

    # Info commands
    if lower.startswith("weather"):
        return handle_weather()

    # Agent commands
    if lower.startswith("pulse"):
        return handle_pulse(lower)
    if lower.startswith("oracle"):
        return handle_oracle(lower)
    if lower.startswith("vibe"):
        return handle_vibe(lower, text)
    if lower.startswith("calendar") or lower.startswith("cal "):
        return handle_calendar(lower, text)
    if lower.startswith("rent"):
        return handle_rent(lower, text)
    if lower.startswith("add project") or lower.startswith("add to "):
        return handle_projects(lower, text)
    if lower.startswith("project"):
        return handle_projects(lower, text)
    if lower.startswith("habit") or lower.startswith("add habit"):
        return handle_habits(lower, text)
    if lower.startswith("order ") or lower.startswith("book "):
        return handle_agent_queue(text)

    if lower in ("help", "commands"):
        return (
            "**Katana Agent Commands**\n\n"
            "**PULSE (Newsletter)**\n"
            "/pulse — Pipeline status\n"
            "/pulse news — Top headlines\n"
            "/pulse stats — Subscriber count\n"
            "/pulse newsletter — Send NL to you\n"
            "/pulse newsletter gen — Generate NL\n"
            "/pulse send — Email to subscribers\n\n"
            "**ORACLE (Astrology)**\n"
            "/oracle — Daily horoscope\n"
            "/oracle week — Week ahead\n"
            "/oracle moon — Moon phase\n"
            "/oracle vibe — Planetary vibe\n\n"
            "**VIBE (Daily Recs)**\n"
            "/vibe — Full daily vibe\n"
            "/vibe food / music / outfit / activity\n\n"
            "**CALENDAR**\n"
            "/calendar — Today's events (Phase 2)\n\n"
            "**RENT (Human Tasks)**\n"
            "/rent — Browse available humans\n"
            "/rent status — Connection check\n"
            "/rent bounties — Browse open bounties/jobs\n"
            "/rent skills — Available skills\n"
            "/rent scan — AI-scored opportunities (48hrs)\n"
            "/rent scan new — Only unseen bounties\n"
            "/rent scan all — Score ALL open bounties\n"
            "/rent scan force — Bypass cache, fresh Grok scoring\n"
            "/rent save <id> — Save a bounty\n"
            "/rent saved — View saved bounties\n"
            "/rent unsave <id> — Remove saved\n"
            "/rent post <desc> — Post a bounty\n\n"
            "**TASKS & GOALS**\n"
            "/tasks — Today's tasks\n"
            "add task: ... — Add task\n"
            "done: ... / done 1 — Complete task\n"
            "/goals — Active goals\n"
            "add goal: ... — Add goal\n"
            "/progress — Today's stats\n"
            "/projects — List projects\n"
            "/project <name> — Show project\n"
            "add project: <name> — Create project\n"
            "add to <project>: <task> — Add to project\n"
            "/habits — Daily habits\n"
            "add habit: ... — Add habit\n"
            "habit done: ... — Complete habit\n"
            "/order <what> — Order (queued)\n"
            "/book <what> — Book (queued)\n\n"
            "**SYSTEM**\n"
            "/help — This menu\n"
            "/status — Listener + health\n"
            "/weather — Current weather\n"
            "sleep / wake — Toggle sleep mode"
        )

    # Fallback — echo that we received it but can't handle it
    return f"Received: \"{text}\"\n(Use /help for available commands)"

# ── Scheduled alerts ────────────────────────────────────────

async def scheduled_alerts(client):
    """Run scheduled alerts (morning brief, evening check-in)."""
    sent_morning = False
    sent_evening = False

    while True:
        now = datetime.now()
        today = now.date()
        profile = load_profile()
        tg_config = profile.get("telegram", {})

        # Morning brief at 8:00 AM
        if not sent_morning and now.hour == 8 and now.minute == 0 and tg_config.get("morning_brief", True):
            weather = handle_weather()
            tracker = get_tracker(profile)
            tasks = tracker.get("tasks", [])
            goals = tracker.get("goals", [])
            task_list = "\n".join(f"  - {t['text']}" for t in tasks) if tasks else "  None yet"
            goal_list = "\n".join(f"  - {g['text']}" for g in goals) if goals else "  None yet"

            msg = (
                f"**Good morning!**\n\n"
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
            done_list = "\n".join(f"  - {t['text']}" for t in done) if done else "  Nothing yet"
            pending_list = "\n".join(f"  - {t['text']}" for t in pending) if pending else "  All done!"

            # Update streak
            if done:
                tracker["streak"] = tracker.get("streak", 0) + 1
            else:
                tracker["streak"] = 0
            save_profile(profile)

            msg = (
                f"**Evening Check-In**\n\n"
                f"Completed today:\n{done_list}\n\n"
                f"Still pending:\n{pending_list}\n\n"
                f"Streak: {tracker.get('streak', 0)} days"
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
                await event.reply(response, parse_mode="md")
            except Exception:
                # Fallback without markdown if parse fails
                await event.reply(response)
            log.info(f"Replied: {response[:80]}...")

    await client.start(bot_token=BOT_TOKEN)
    me = await client.get_me()
    log.info(f"Telegram bot started as @{me.username} (ID: {me.id})")
    log.info(f"Listening for messages from user ID: {USER_ID}")

    write_pid()
    save_state({"sleeping": False, "sleep_until": None})

    # Send startup notification
    try:
        await client.send_message(USER_ID, "Telegram listener is now active. Say 'help' for commands.", parse_mode="md")
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
            os.setsid()
            asyncio.run(run_listener())
            return

    # Foreground mode
    def handle_shutdown(sig, frame):
        log.info("Shutting down...")
        clear_pid()
        sys.exit(0)

    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)

    try:
        asyncio.run(run_listener())
    except KeyboardInterrupt:
        log.info("Interrupted")
    finally:
        clear_pid()

if __name__ == "__main__":
    main()
