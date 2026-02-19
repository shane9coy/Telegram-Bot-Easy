#!/usr/bin/env python3
"""
Telegram Bot Helper Functions

Pure-Python helpers for the Telegram listener daemon.
No MCP or Claude dependencies — only stdlib, requests, supabase.

Built by: x.com/@shaneswrld_ | github.com/shane9coy
"""

import os
import json
import math
import random
import hashlib
from datetime import datetime, date, timedelta
from pathlib import Path

import requests
from dotenv import load_dotenv

# ── Config ──────────────────────────────────────────────────
PROJECT_DIR = Path(__file__).parent
load_dotenv(PROJECT_DIR / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
RENTAHUMAN_API_KEY = os.getenv("RENTAHUMAN_API_KEY", "")
RENTAHUMAN_BASE = "https://rentahuman.ai/api"
RENTAHUMAN_WEB = "https://rentahuman.ai"

RANKED_NEWS_DIR = PROJECT_DIR / "news_letter" / "ranked_news"
FINAL_EMAIL_DIR = PROJECT_DIR / "news_letter" / "final_email"
PROFILE_PATH = PROJECT_DIR / ".claude" / "user_profile.json"


def _load_profile():
    try:
        return json.loads(PROFILE_PATH.read_text())
    except Exception:
        return {}


# ═══════════════════════════════════════════════════════════
#  PULSE HELPERS
# ═══════════════════════════════════════════════════════════

def get_pulse_status(date_str=None):
    """Check if ranked_news + final_email files exist for date."""
    date_str = date_str or date.today().isoformat()
    ranked = RANKED_NEWS_DIR / f"ranked_news_{date_str}.json"
    email = FINAL_EMAIL_DIR / f"email_newsletter_final_{date_str}.html"
    lines = [f"**Pulse Status — {date_str}**"]
    lines.append(f"Ranked news: {'found' if ranked.exists() else 'not found'}")
    lines.append(f"Final email: {'found' if email.exists() else 'not found'}")
    if ranked.exists():
        try:
            data = json.loads(ranked.read_text())
            count = len(data.get("top_stories", []))
            lines.append(f"Stories ranked: {count}")
        except Exception:
            pass
    return "\n".join(lines)


def get_top_headlines(date_str=None, n=5):
    """Parse ranked_news JSON, return top N headlines."""
    date_str = date_str or date.today().isoformat()
    path = RANKED_NEWS_DIR / f"ranked_news_{date_str}.json"
    if not path.exists():
        return f"No ranked news found for {date_str}."
    try:
        data = json.loads(path.read_text())
        stories = data.get("top_stories", [])[:n]
        if not stories:
            return "No stories in ranked news file."
        lines = [f"**Top {len(stories)} Headlines — {date_str}**", ""]
        for s in stories:
            lines.append(f"{s.get('rank', '?')}. {s.get('headline', 'No headline')}")
        return "\n".join(lines)
    except Exception as e:
        return f"Error reading ranked news: {e}"


def get_subscriber_stats():
    """Query Supabase leads table for newsletter opt-in count."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        return "Supabase not configured."
    try:
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
        }
        url = f"{SUPABASE_URL}/rest/v1/leads?newsletter_optin=eq.true&select=id"
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        count = len(r.json())
        return f"**Subscriber Stats**\nNewsletter opt-ins: {count}"
    except Exception as e:
        return f"Stats error: {e}"


def get_newsletter_html(date_str=None):
    """Read final_email HTML content for sending via Telegram."""
    date_str = date_str or date.today().isoformat()
    path = FINAL_EMAIL_DIR / f"email_newsletter_final_{date_str}.html"
    if not path.exists():
        return None
    try:
        return path.read_text()
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════
#  ORACLE HELPERS
# ═══════════════════════════════════════════════════════════

# Known new moon reference: Jan 29, 2025 12:36 UTC
_NEW_MOON_REF = datetime(2025, 1, 29, 12, 36)
_SYNODIC_PERIOD = 29.53059

MOON_PHASES = [
    (0.0,   "New Moon",        "Plant seeds. Set intentions."),
    (0.125, "Waxing Crescent", "Take first steps. Build momentum."),
    (0.25,  "First Quarter",   "Push through resistance. Commit."),
    (0.375, "Waxing Gibbous",  "Refine and adjust. Almost there."),
    (0.5,   "Full Moon",       "Peak energy. Harvest results."),
    (0.625, "Waning Gibbous",  "Share wisdom. Give back."),
    (0.75,  "Last Quarter",    "Release what doesn't serve you."),
    (0.875, "Waning Crescent", "Rest. Reflect. Prepare for renewal."),
]

SIGN_THEMES = {
    "Aries":       "Bold action and new beginnings",
    "Taurus":      "Grounding, stability, sensual pleasures",
    "Gemini":      "Communication, curiosity, mental agility",
    "Cancer":      "Emotional depth, nurturing, home focus",
    "Leo":         "Creative expression, confidence, leadership",
    "Virgo":       "Organization, health, detail-oriented service",
    "Libra":       "Balance, partnerships, aesthetic harmony",
    "Scorpio":     "Transformation, intensity, deep truth",
    "Sagittarius": "Expansion, adventure, philosophical growth",
    "Capricorn":   "Discipline, ambition, long-term building",
    "Aquarius":    "Innovation, community, breaking patterns",
    "Pisces":      "Intuition, spirituality, creative flow",
}

DAY_ENERGY = {
    0: ("Monday",    "Moon day — emotions, intuition, inner work"),
    1: ("Tuesday",   "Mars day — action, courage, physical energy"),
    2: ("Wednesday", "Mercury day — communication, learning, deals"),
    3: ("Thursday",  "Jupiter day — expansion, luck, big-picture thinking"),
    4: ("Friday",    "Venus day — love, beauty, creativity, connection"),
    5: ("Saturday",  "Saturn day — discipline, structure, long-term plans"),
    6: ("Sunday",    "Sun day — vitality, self-expression, joy"),
}

# Sign-specific daily horoscope readings (deterministic pick per day)
SIGN_DAILY_READINGS = {
    "Aries": [
        "A bold opportunity presents itself — trust your instincts and move quickly. Your competitive edge is sharp today.",
        "Channel that fire energy into a passion project. Others are drawn to your confidence right now.",
        "Patience isn't your forte, but today rewards those who wait. Strategic timing beats raw speed.",
        "Your leadership is needed. Step up and take charge of a situation others are avoiding.",
        "Physical energy is through the roof — hit the gym, start that project, or have the hard conversation.",
        "A conflict may arise, but it's a chance to grow. Stand your ground without burning bridges.",
        "Spontaneity leads to something unexpectedly good today. Say yes to the thing that scares you.",
    ],
    "Taurus": [
        "Financial matters are highlighted — a good day to review budgets, investments, or that purchase you've been eyeing.",
        "Comfort is calling. Honor your need for stability, but don't let it become stagnation.",
        "Your patience pays off today. Something you've been building steadily finally shows results.",
        "Sensory pleasures are amplified — good food, good music, nature. Indulge mindfully.",
        "Stubbornness could be your enemy today. Consider that the other person might have a point.",
        "A material opportunity emerges. Your eye for quality and value gives you an advantage.",
        "Slow down and savor the moment. Not everything needs to be productive — rest is productive too.",
    ],
    "Gemini": [
        "Your words carry extra weight today. A conversation could shift the direction of a relationship or project.",
        "Information overload is possible — filter the noise and focus on what actually matters.",
        "Social energy is high. Networking, reconnecting, or meeting someone new could be significant.",
        "Your curiosity leads you somewhere unexpected. Follow that rabbit hole — it's worth it.",
        "Multitasking is tempting but depth beats breadth today. Pick one thing and go deep.",
        "A message or piece of news arrives that changes your perspective. Stay open-minded.",
        "Your adaptability is your superpower today. Others are rigid — you can flow around obstacles.",
    ],
    "Cancer": [
        "Home and family matters take center stage. A nurturing gesture goes further than you think.",
        "Your intuition is razor-sharp today. That gut feeling? Trust it completely.",
        "Emotional boundaries need attention. It's okay to take care of yourself before others.",
        "A memory or nostalgia sparks insight about a current situation. The past has a lesson.",
        "Your empathy draws someone to confide in you. Listening is the greatest gift today.",
        "Domestic projects thrive — cooking, decorating, organizing. Create comfort in your space.",
        "Vulnerability is strength today. Sharing how you feel opens a door that's been closed.",
    ],
    "Leo": [
        "The spotlight finds you naturally today. Use the attention to uplift others, not just yourself.",
        "Creative expression is your medicine. Write, draw, perform, or simply let your personality shine.",
        "A leadership opportunity emerges. Your warmth and confidence inspire others to follow.",
        "Romance or creative passion is amplified. Heart-centered pursuits are deeply rewarding.",
        "Pride might be tested — the graceful response is the powerful one. Rise above pettiness.",
        "Generosity returns to you tenfold today. Give freely of your time, energy, or resources.",
        "Your inner child wants to play. Joy and fun aren't frivolous — they're essential fuel.",
    ],
    "Virgo": [
        "Details matter today more than usual. Your analytical eye catches something others miss.",
        "Health and wellness routines are especially powerful now. Small habits compound into big results.",
        "A problem that's been nagging you finally has a clear solution. Trust your methodical approach.",
        "Service to others brings unexpected fulfillment. Help without expecting recognition.",
        "Perfectionism could paralyze you — done is better than perfect. Ship it.",
        "Organization and planning pay off. Tidy your space, tidy your mind.",
        "Your practical wisdom is exactly what someone needs to hear. Don't hold back your advice.",
    ],
    "Libra": [
        "Relationships are the focal point — a partnership decision or deepening connection is likely.",
        "Your aesthetic sense is heightened. Beauty, art, and design feed your soul today.",
        "Diplomacy is your superpower. You can bridge a gap that others can't even see.",
        "Balance is off — check if you're giving too much or too little. Recalibrate.",
        "A social situation requires your charm and grace. You navigate it effortlessly.",
        "Justice or fairness issues arise. Your balanced perspective is needed.",
        "Indecision may haunt you — set a timer, make the call, and trust it. Both options are good.",
    ],
    "Scorpio": [
        "Transformation energy is intense today. Something old must die for something new to be born.",
        "Your investigative instincts uncover a truth that's been hidden. Use this knowledge wisely.",
        "Emotional depth is your strength — a profound connection or realization is possible.",
        "Power dynamics are at play. Choose empowerment over control, for yourself and others.",
        "Let go of something you've been gripping too tightly. The release brings unexpected relief.",
        "Your intensity is magnetic today. Channel it into work that matters to you.",
        "Trust is the theme — either building it or deciding who deserves it. Your instincts know.",
    ],
    "Sagittarius": [
        "Adventure calls — even a small one. Break routine and explore something unfamiliar.",
        "A philosophical insight or learning moment expands your worldview. Share what you discover.",
        "Optimism is your fuel today. Your enthusiasm is contagious and opens doors.",
        "Travel or foreign connections are highlighted. A distant perspective offers clarity.",
        "Honesty is essential but delivery matters. Blunt truth wrapped in kindness lands better.",
        "Freedom needs defending today. Don't let obligations box in your spirit.",
        "A big-picture vision crystallizes. You see where you're headed and it excites you.",
    ],
    "Capricorn": [
        "Ambition and strategy align perfectly today. Make moves toward your long-term goals.",
        "Your discipline is admired. A structured approach to chaos creates order where others can't.",
        "Career or reputation matters are prominent. Your professionalism speaks volumes.",
        "Patience with the process pays dividends. The mountain is climbed one step at a time.",
        "Authority or mentorship is highlighted — either receiving wisdom or sharing your own.",
        "Practical solutions win over idealistic ones today. Stay grounded in what works.",
        "Allow yourself to relax. Even Capricorns need to put down the weight sometimes.",
    ],
    "Aquarius": [
        "Innovation strikes — a unique idea or unconventional approach solves a stubborn problem.",
        "Community and friendship are highlighted. Your people need you, and you need them.",
        "Rebel energy is strong. Question the status quo, but offer alternatives, not just critique.",
        "Technology or future-forward thinking gives you an edge today.",
        "Humanitarian impulses are strong. Find a way to make the world slightly better.",
        "Your individuality is your strength. Don't dim your weirdness to fit in.",
        "Detachment serves you today. Observe before reacting. Emotional distance brings clarity.",
    ],
    "Pisces": [
        "Intuition and creativity are at peak levels. Artistic or spiritual work flows effortlessly.",
        "Dreams and subconscious messages carry important information. Pay attention to symbols.",
        "Compassion is boundless today, but protect your energy. Absorbing others' pain helps no one.",
        "A spiritual or mystical experience is possible. Stay open to the unseen.",
        "Music, water, or nature restores you profoundly. Seek these elements today.",
        "Boundaries are blurry — clarify where you end and others begin. It's an act of love.",
        "Your imagination turns an ordinary situation into something magical. See the wonder.",
    ],
}

# Upcoming astronomical/astrological events (approximate 2026 dates)
ASTRO_EVENTS_2026 = [
    ("2026-01-13", "New Moon in Capricorn — Set ambitious goals, structure new foundations"),
    ("2026-01-27", "Full Moon in Leo — Creative expression peaks, spotlight on passion"),
    ("2026-02-11", "New Moon in Aquarius — Innovation energy, community-focused intentions"),
    ("2026-02-25", "Full Moon in Virgo — Harvest health routines, organize and refine"),
    ("2026-03-01", "Venus enters Aries — Bold moves in love and money"),
    ("2026-03-13", "New Moon in Pisces — Spiritual reset, intuition amplified"),
    ("2026-03-17", "Mercury enters Aries — Direct communication, fast thinking"),
    ("2026-03-27", "Full Moon in Libra — Relationship culminations, seeking balance"),
    ("2026-04-11", "New Moon in Aries — Powerful new beginnings, fresh starts"),
    ("2026-04-25", "Full Moon in Scorpio — Deep emotional revelations, transformation"),
    ("2026-05-11", "New Moon in Taurus — Financial intentions, grounding energy"),
    ("2026-05-25", "Full Moon in Sagittarius — Expansion, travel, philosophical breakthroughs"),
    ("2026-06-10", "New Moon in Gemini — Communication reset, new connections"),
    ("2026-06-23", "Full Moon in Capricorn — Career milestones, authority recognition"),
    ("2026-07-10", "New Moon in Cancer — Home and family intentions, emotional renewal"),
    ("2026-07-23", "Full Moon in Aquarius — Community achievements, humanitarian progress"),
    ("2026-07-26", "Mercury Retrograde begins in Leo — Review creative projects, revisit self-expression"),
    ("2026-08-20", "Mercury Retrograde ends — Clear to move forward on delayed plans"),
    ("2026-08-08", "New Moon in Leo — Creative new beginnings, confidence boost"),
    ("2026-08-22", "Full Moon in Pisces — Spiritual culmination, release and surrender"),
    ("2026-09-07", "New Moon in Virgo — Health resets, detailed planning pays off"),
    ("2026-09-21", "Full Moon in Aries — Bold completions, courage rewarded"),
    ("2026-10-06", "New Moon in Libra — Partnership intentions, harmony-seeking"),
    ("2026-10-21", "Full Moon in Taurus — Material harvest, financial culmination"),
    ("2026-11-05", "New Moon in Scorpio — Powerful transformation cycle begins"),
    ("2026-11-19", "Full Moon in Gemini — Communication breakthroughs, truth emerges"),
    ("2026-11-20", "Mercury Retrograde begins in Sagittarius — Review travel plans, belief systems"),
    ("2026-12-04", "New Moon in Sagittarius — Adventurous new intentions, expansion"),
    ("2026-12-10", "Mercury Retrograde ends — Green light for decisions and contracts"),
    ("2026-12-19", "Full Moon in Cancer — Emotional peak, family connections"),
]


def get_moon_phase(dt=None):
    """Calculate current moon phase from synodic cycle."""
    dt = dt or datetime.now()
    days_since = (dt - _NEW_MOON_REF).total_seconds() / 86400
    cycle_pos = (days_since % _SYNODIC_PERIOD) / _SYNODIC_PERIOD
    # Find closest phase
    phase_name, energy = "Unknown", ""
    for i, (threshold, name, desc) in enumerate(MOON_PHASES):
        next_threshold = MOON_PHASES[i + 1][0] if i + 1 < len(MOON_PHASES) else 1.0
        if threshold <= cycle_pos < next_threshold:
            phase_name, energy = name, desc
            break
    pct = round(cycle_pos * 100)
    return f"**Moon Phase**\n{phase_name} ({pct}% through cycle)\n{energy}"


def _day_seed(dt=None):
    """Deterministic seed from date for consistent daily outputs."""
    dt = dt or date.today()
    return int(hashlib.md5(dt.isoformat().encode()).hexdigest(), 16)


def _get_phase_info(dt=None):
    """Return (phase_name, phase_energy, cycle_pos) for a datetime."""
    dt = dt or datetime.now()
    days_since = (dt - _NEW_MOON_REF).total_seconds() / 86400
    cycle_pos = (days_since % _SYNODIC_PERIOD) / _SYNODIC_PERIOD
    phase_name, phase_energy = "New Moon", "Set intentions."
    for i, (threshold, name, desc) in enumerate(MOON_PHASES):
        next_t = MOON_PHASES[i + 1][0] if i + 1 < len(MOON_PHASES) else 1.0
        if threshold <= cycle_pos < next_t:
            phase_name, phase_energy = name, desc
            break
    return phase_name, phase_energy, cycle_pos


def _get_upcoming_astro_events(n=3):
    """Return the next N upcoming astrological events."""
    today = date.today().isoformat()
    upcoming = [e for e in ASTRO_EVENTS_2026 if e[0] >= today]
    return upcoming[:n]


def get_daily_horoscope(profile=None):
    """Full daily reading: sign-specific horoscope + placements + upcoming events."""
    profile = profile or _load_profile()
    calc = profile.get("birth_chart", {}).get("calculated", {})
    sun = calc.get("sun_sign", "Scorpio")
    moon = calc.get("moon_sign", "Gemini")
    rising = calc.get("rising_sign", "Libra")

    seed = _day_seed()
    rng = random.Random(seed)

    sun_theme = SIGN_THEMES.get(sun, "Unknown energy")
    moon_theme = SIGN_THEMES.get(moon, "Unknown energy")
    rising_theme = SIGN_THEMES.get(rising, "Unknown energy")

    # Moon phase
    phase_name, phase_energy, cycle_pos = _get_phase_info()

    # Sign-specific daily reading
    sun_readings = SIGN_DAILY_READINGS.get(sun, ["Trust the process today."])
    moon_readings = SIGN_DAILY_READINGS.get(moon, ["Stay curious."])
    rising_readings = SIGN_DAILY_READINGS.get(rising, ["Show up as yourself."])
    sun_reading = rng.choice(sun_readings)
    moon_reading = rng.choice(moon_readings)
    rising_reading = rng.choice(rising_readings)

    focuses = [
        "creative projects", "deep conversations", "physical movement",
        "financial planning", "self-care rituals", "learning something new",
        "connecting with others", "solo reflection", "tackling your hardest task first",
        "slowing down and being present",
    ]
    focus = rng.choice(focuses)

    energies = ["high", "moderate", "building", "steady", "electric", "calm but focused"]
    energy = rng.choice(energies)

    # Day energy
    day_name, day_desc = DAY_ENERGY.get(datetime.now().weekday(), ("?", ""))

    # Upcoming events
    upcoming = _get_upcoming_astro_events(3)

    lines = [
        f"**Daily Horoscope — {date.today().strftime('%b %d')}**",
        f"Sun in {sun} · Moon in {moon} · Rising {rising}",
        f"{day_name}: {day_desc}",
        "",
        f"**Moon: {phase_name}** ({round(cycle_pos * 100)}%)",
        phase_energy,
        "",
        f"**{sun} Sun**",
        f"{sun_theme}",
        f"{sun_reading}",
        "",
        f"**{moon} Moon**",
        f"{moon_theme}",
        f"{moon_reading}",
        "",
        f"**{rising} Rising**",
        f"{rising_theme}",
        f"{rising_reading}",
        "",
        f"Energy: {energy} | Focus: {focus}",
    ]

    if upcoming:
        lines.append("")
        lines.append("**Coming Up**")
        for evt_date, evt_desc in upcoming:
            d = date.fromisoformat(evt_date)
            delta = (d - date.today()).days
            when = "Today" if delta == 0 else f"Tomorrow" if delta == 1 else f"In {delta}d"
            lines.append(f"• {when} ({d.strftime('%b %d')}): {evt_desc}")

    return "\n".join(lines)


def get_weekly_outlook(profile=None):
    """7-day outlook based on sign themes + moon phases."""
    profile = profile or _load_profile()
    calc = profile.get("birth_chart", {}).get("calculated", {})
    sun = calc.get("sun_sign", "Scorpio")

    today = date.today()
    lines = [f"**Week Ahead — {sun}**", ""]

    for offset in range(7):
        day = today + timedelta(days=offset)
        day_name, day_desc = DAY_ENERGY.get(day.weekday(), ("?", ""))
        dt = datetime(day.year, day.month, day.day, 12, 0)
        days_since = (dt - _NEW_MOON_REF).total_seconds() / 86400
        cycle_pos = (days_since % _SYNODIC_PERIOD) / _SYNODIC_PERIOD
        phase = "New Moon"
        for i, (threshold, name, _) in enumerate(MOON_PHASES):
            next_t = MOON_PHASES[i + 1][0] if i + 1 < len(MOON_PHASES) else 1.0
            if threshold <= cycle_pos < next_t:
                phase = name
                break
        label = "Today" if offset == 0 else day_name
        lines.append(f"**{label} ({day.strftime('%b %d')}):** {phase} — {day_desc}")

    return "\n".join(lines)


def get_oracle_vibe():
    """Planetary vibe: moon phase + day-of-week energy + sign themes."""
    now = datetime.now()
    day_name, day_desc = DAY_ENERGY.get(now.weekday(), ("?", ""))
    moon = get_moon_phase(now)

    seed = _day_seed()
    rng = random.Random(seed)
    signs = list(SIGN_THEMES.keys())
    dominant = rng.choice(signs)

    lines = [
        f"**Planetary Vibe**",
        "",
        moon,
        "",
        f"**{day_name}:** {day_desc}",
        f"**Dominant energy:** {dominant} — {SIGN_THEMES[dominant]}",
    ]
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════
#  VIBE HELPERS
# ═══════════════════════════════════════════════════════════

def get_vibe_food(profile=None):
    """Random cuisine pick from preferences."""
    profile = profile or _load_profile()
    cuisines = profile.get("preferred_food", {}).get("food", {}).get("cuisines", [])
    if not cuisines:
        return "No food preferences set. Update your profile!"
    seed = _day_seed()
    rng = random.Random(seed)
    pick = rng.choice(cuisines)
    dislikes = profile.get("preferred_food", {}).get("food", {}).get("dislikes", [])
    note = f" (avoid: {', '.join(dislikes)})" if dislikes else ""
    return f"**Food Vibe**\nToday's pick: {pick}{note}"


def get_vibe_music(profile=None):
    """Random genre pick from preferences."""
    profile = profile or _load_profile()
    genres = profile.get("preferred_music", {}).get("music_types", [])
    if not genres:
        return "No music preferences set. Update your profile!"
    seed = _day_seed()
    rng = random.Random(seed)
    pick = rng.choice(genres)
    artists = profile.get("preferred_music", {}).get("artists", [])
    artist_names = [a.get("name", "") for a in artists if a.get("name")]
    artist_note = f"\nArtist to try: {rng.choice(artist_names)}" if artist_names else ""
    return f"**Music Vibe**\nGenre: {pick}{artist_note}"


def get_vibe_outfit(weather_text=None):
    """Clothing rec based on temperature extracted from weather text."""
    if not weather_text:
        weather_text = _fetch_weather_text()
    # Try to extract temp from "XF" pattern
    temp = None
    for word in weather_text.replace("(", " ").replace(")", " ").split():
        if word.endswith("F") and word[:-1].replace("-", "").replace(".", "").isdigit():
            temp = float(word[:-1])
            break
    if temp is None:
        return "**Outfit Vibe**\nCouldn't parse temperature. Check /weather first."
    if temp < 32:
        outfit = "Heavy coat, layers, scarf, gloves. Bundle up."
    elif temp < 50:
        outfit = "Warm jacket, sweater, long pants. Layer up."
    elif temp < 65:
        outfit = "Light jacket or hoodie. Comfortable layers."
    elif temp < 80:
        outfit = "T-shirt weather. Light and breezy."
    else:
        outfit = "Shorts and tank top. Stay cool, stay hydrated."
    return f"**Outfit Vibe** ({temp:.0f}F)\n{outfit}"


def get_vibe_activity(profile=None):
    """Activity pick from preferences, weather-aware."""
    profile = profile or _load_profile()
    activities = profile.get("preferred_activities", {}).get("activities", [])
    places = profile.get("preferred_activities", {}).get("places", [])
    if not activities:
        return "No activity preferences set. Update your profile!"
    seed = _day_seed()
    rng = random.Random(seed)
    pick = rng.choice(activities)
    place = rng.choice(places) if places else None
    lines = [f"**Activity Vibe**", f"Do this: {pick.get('name', pick) if isinstance(pick, dict) else pick}"]
    if place:
        lines.append(f"Where: {place.get('name', place) if isinstance(place, dict) else place}")
    return "\n".join(lines)


def get_simple_vibe(profile=None, weather_text=None):
    """Full vibe: food + music + activity + oracle vibe."""
    profile = profile or _load_profile()
    weather_text = weather_text or _fetch_weather_text()
    parts = [
        f"**Daily Vibe Check**\n",
        weather_text,
        "",
        get_oracle_vibe(),
        "",
        get_vibe_food(profile),
        "",
        get_vibe_music(profile),
        "",
        get_vibe_activity(profile),
        "",
        get_vibe_outfit(weather_text),
    ]
    return "\n".join(parts)


def _fetch_weather_text():
    """Quick weather fetch for internal use."""
    profile = _load_profile()
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
        return f"Weather unavailable: {e}"


# ═══════════════════════════════════════════════════════════
#  RENT HELPERS
# ═══════════════════════════════════════════════════════════

def _rent_headers():
    return {
        "X-API-Key": RENTAHUMAN_API_KEY,
        "Content-Type": "application/json",
    }


def rent_list_humans():
    """GET /api/humans — list available humans."""
    if not RENTAHUMAN_API_KEY:
        return "RentAHuman API key not configured. Add RENTAHUMAN_API_KEY to .env."
    try:
        r = requests.get(f"{RENTAHUMAN_BASE}/humans", headers=_rent_headers(), timeout=10)
        r.raise_for_status()
        data = r.json()
        humans = data.get("humans", [])
        if not humans:
            return "No humans available."
        lines = ["**Available Humans**", ""]
        for h in humans[:10]:
            hid = h.get("id", "")
            name = h.get("name", "Unknown")
            skills = h.get("skills", [])
            rate = h.get("hourlyRate", "?")
            city = h.get("location", {}).get("city", "?")
            top_skills = ", ".join(skills[:3]) if skills else "General"
            link = f"{RENTAHUMAN_WEB}/humans/{hid}" if hid else ""
            lines.append(f"• [{name}]({link}) ({city}) — ${rate}/hr")
            lines.append(f"  {top_skills}")
        lines.append("")
        lines.append("Use `/rent bounties` to browse jobs, `/rent post <desc>` to create one.")
        return "\n".join(lines)
    except requests.exceptions.HTTPError as e:
        return f"RentAHuman API error: {e.response.status_code}"
    except Exception as e:
        return f"RentAHuman error: {e}"


def rent_list_bounties():
    """GET /api/bounties — browse available bounties/jobs."""
    if not RENTAHUMAN_API_KEY:
        return "RentAHuman API key not configured."
    try:
        r = requests.get(f"{RENTAHUMAN_BASE}/bounties", headers=_rent_headers(), timeout=10)
        r.raise_for_status()
        data = r.json()
        bounties = data.get("bounties", [])
        if not bounties:
            return "No open bounties."
        lines = ["**Open Bounties**", ""]
        for b in bounties[:10]:
            bid = b.get("id", "")
            title = b.get("title", "Untitled")
            status = b.get("status", "open")
            price = b.get("price", "?")
            category = b.get("category", "")
            spots = b.get("spotsAvailable", "?")
            agent = b.get("agentName", "")
            link = f"{RENTAHUMAN_WEB}/bounties/{bid}" if bid else ""
            lines.append(f"• [{title}]({link}) — ${price} ({status})")
            detail_parts = []
            if agent:
                detail_parts.append(f"By: {agent}")
            if category:
                detail_parts.append(f"Category: {category}")
            detail_parts.append(f"Spots: {spots}")
            lines.append(f"  {' | '.join(detail_parts)}")
        return "\n".join(lines)
    except requests.exceptions.HTTPError as e:
        return f"RentAHuman API error: {e.response.status_code}"
    except Exception as e:
        return f"RentAHuman error: {e}"


def rent_list_skills():
    """GET /api/humans — list humans grouped by skills."""
    if not RENTAHUMAN_API_KEY:
        return "RentAHuman API key not configured."
    try:
        r = requests.get(f"{RENTAHUMAN_BASE}/humans", headers=_rent_headers(), timeout=10)
        r.raise_for_status()
        data = r.json()
        humans = data.get("humans", [])
        if not humans:
            return "No humans found."
        # Collect all unique skills
        all_skills = {}
        for h in humans:
            for skill in h.get("skills", []):
                all_skills.setdefault(skill, []).append(h.get("name", "?"))
        lines = ["**Available Skills**", ""]
        for skill, names in sorted(all_skills.items()):
            search_url = f"{RENTAHUMAN_WEB}/browse?q={skill.replace(' ', '+')}"
            count = len(names)
            lines.append(f"• [{skill}]({search_url}) ({count} human{'s' if count > 1 else ''})")
        return "\n".join(lines)
    except Exception as e:
        return f"RentAHuman error: {e}"


def rent_status():
    """Check RentAHuman API connection and key validity."""
    if not RENTAHUMAN_API_KEY:
        return "RentAHuman API key not configured. Add RENTAHUMAN_API_KEY to .env."
    try:
        r = requests.get(f"{RENTAHUMAN_BASE}/humans", headers=_rent_headers(), timeout=10)
        r.raise_for_status()
        humans = r.json().get("humans", [])
        r2 = requests.get(f"{RENTAHUMAN_BASE}/bounties", headers=_rent_headers(), timeout=10)
        r2.raise_for_status()
        bounties = r2.json().get("bounties", [])
        key_preview = RENTAHUMAN_API_KEY[:8] + "..." if len(RENTAHUMAN_API_KEY) > 8 else "***"
        return (
            f"**RentAHuman Status**\n"
            f"API: connected\n"
            f"Key: {key_preview}\n"
            f"Humans available: {len(humans)}\n"
            f"Open bounties: {len(bounties)}"
        )
    except requests.exceptions.HTTPError as e:
        return f"**RentAHuman Status**\nAPI error: {e.response.status_code}"
    except Exception as e:
        return f"**RentAHuman Status**\nConnection failed: {e}"


def rent_create_bounty(title, desc, budget=None):
    """POST /api/bookings — create a new bounty."""
    if not RENTAHUMAN_API_KEY:
        return "RentAHuman API key not configured."
    payload = {
        "title": title,
        "description": desc,
        "agentType": "claude",
    }
    if budget:
        payload["price"] = budget
        payload["priceType"] = "fixed"
    try:
        r = requests.post(f"{RENTAHUMAN_BASE}/bookings", json=payload,
                          headers=_rent_headers(), timeout=10)
        r.raise_for_status()
        return f"Bounty created: {title}"
    except Exception as e:
        return f"Failed to create bounty: {e}"
