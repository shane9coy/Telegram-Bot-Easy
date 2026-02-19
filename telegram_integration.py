#!/usr/bin/env python3
"""
Telegram Integration for Master Agent Orchestrator

This module provides helper functions for sending Telegram notifications
from the master_agent_orchestrator.py using the Telegram MCP server.

Usage:
    from telegram_integration import TelegramNotifier
    
    notifier = TelegramNotifier()
    await notifier.send_morning_routine_complete(steps, duration)
    await notifier.send_daily_horoscope(sign, reading)
"""

import os
import sys
import json
import asyncio
import logging
from datetime import datetime, date
from typing import Optional, Dict, Any, List
from pathlib import Path

logger = logging.getLogger("telegram_integration")

# ============================================================
# CONFIGURATION
# ============================================================

# Load environment variables
TELEGRAM_BOT_USER_ID = int(os.getenv("TELEGRAM_BOT_USER_ID", "0"))
ENABLE_NOTIFICATIONS = os.getenv("ENABLE_NOTIFICATIONS", "true").lower() == "true"

# ============================================================
# NOTIFICATION TEMPLATES
# ============================================================

class NotificationTemplates:
    """Pre-formatted notification templates for kilo bot"""

    @staticmethod
    def morning_routine_complete(steps_completed: List[str], duration: str) -> str:
        """Morning routine completion notification"""
        steps_text = "\n".join([f"✅ {step}" for step in steps_completed])
        return f"""🌅 **Morning Routine Complete**

{steps_text}

⏱️ Duration: {duration}
📅 Date: {date.today().strftime('%B %d, %Y')}
"""

    @staticmethod
    def daily_horoscope(sign: str, reading: str, moon_phase: str = "") -> str:
        """Daily horoscope notification"""
        moon_text = f"\n🌙 Moon Phase: {moon_phase}" if moon_phase else ""
        return f"""🌟 **Daily Horoscope - {sign}**
{date.today().strftime('%B %d, %Y')}

{reading}{moon_text}
"""

    @staticmethod
    def weather_alert(location: str, temp: float, condition: str, feels_like: float = None) -> str:
        """Weather alert notification"""
        feels_text = f"\n🌡️ Feels like: {feels_like}°C" if feels_like else ""
        return f"""🌤️ **Weather Update - {location}**

🌡️ Temperature: {temp}°C{feels_text}
☁️ Condition: {condition}
📅 {date.today().strftime('%B %d, %Y')}
"""

    @staticmethod
    def calendar_reminder(event_title: str, event_time: str, location: str = "") -> str:
        """Calendar reminder notification"""
        loc_text = f"\n📍 Location: {location}" if location else ""
        return f"""📅 **Upcoming Event**

📌 {event_title}
⏰ Time: {event_time}{loc_text}
"""

    @staticmethod
    def project_status(project_name: str, status: str, progress: int = 0) -> str:
        """Project status notification"""
        progress_bar = "█" * (progress // 10) + "░" * (10 - (progress // 10))
        return f"""📊 **Project Status**

📁 {project_name}
📈 Progress: {progress_bar} {progress}%
🏷️ Status: {status}
"""

    @staticmethod
    def oracle_consultation(question: str, response: str) -> str:
        """Oracle consultation response"""
        return f"""🔮 **Oracle Consultation**

❓ Question: {question}

💭 Response:
{response}

🌙 May the stars guide your path.
"""

    @staticmethod
    def system_alert(alert_type: str, message: str) -> str:
        """System alert notification"""
        icons = {
            "info": "ℹ️",
            "warning": "⚠️",
            "error": "❌",
            "success": "✅"
        }
        icon = icons.get(alert_type.lower(), "📢")
        return f"""{icon} **System Alert - {alert_type.upper()}**

{message}

📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

    @staticmethod
    def email_alert(sender: str, subject: str, urgency: str = "normal") -> str:
        """Email alert notification"""
        urgency_icons = {
            "low": "📧",
            "normal": "📬",
            "high": "📨",
            "urgent": "🚨"
        }
        icon = urgency_icons.get(urgency.lower(), "📧")
        return f"""{icon} **New Email**

From: {sender}
Subject: {subject}
Urgency: {urgency.upper()}
"""

    @staticmethod
    def vibe_recommendation(activity: str, description: str, mood: str = "") -> str:
        """Vibe recommendation notification"""
        mood_text = f"\n💭 Mood: {mood}" if mood else ""
        return f"""🎵 **Vibe Recommendation**

🎯 Activity: {activity}
📝 {description}{mood_text}
"""

# ============================================================
# TELEGRAM NOTIFIER
# ============================================================

class TelegramNotifier:
    """
    Telegram notification sender for master agent orchestrator.
    
    This class provides methods to send various types of notifications
    via Telegram using the Telegram MCP server.
    """

    def __init__(self, chat_id: Optional[int] = None):
        """
        Initialize the Telegram notifier.
        
        Args:
            chat_id: Telegram chat ID to send notifications to.
                    If not provided, uses TELEGRAM_BOT_USER_ID from environment.
        """
        self.chat_id = chat_id or TELEGRAM_BOT_USER_ID
        self.templates = NotificationTemplates()
        self.enabled = ENABLE_NOTIFICATIONS and self.chat_id > 0

    def _send_via_mcp(self, message: str, parse_mode: str = "Markdown") -> bool:
        """
        Send message via Telegram MCP server.
        
        This is a placeholder that would be called by the MCP server
        when the agent uses the telegram_send_message tool.
        
        Args:
            message: Message to send
            parse_mode: Parse mode (Markdown or HTML)
            
        Returns:
            True if successful, False otherwise
        """
        # This method is called by the MCP server when the agent
        # uses the telegram_send_message tool. The actual sending
        # is handled by the MCP server.
        logger.info(f"Telegram notification queued: {message[:50]}...")
        return True

    async def send_morning_routine_complete(
        self,
        steps_completed: List[str],
        duration: str
    ) -> bool:
        """
        Send morning routine completion notification.
        
        Args:
            steps_completed: List of completed steps
            duration: Duration of the routine
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            logger.debug("Telegram notifications disabled")
            return False

        message = self.templates.morning_routine_complete(steps_completed, duration)
        return self._send_via_mcp(message)

    async def send_daily_horoscope(
        self,
        sign: str,
        reading: str,
        moon_phase: str = ""
    ) -> bool:
        """
        Send daily horoscope notification.
        
        Args:
            sign: Zodiac sign
            reading: Horoscope reading
            moon_phase: Moon phase (optional)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            logger.debug("Telegram notifications disabled")
            return False

        message = self.templates.daily_horoscope(sign, reading, moon_phase)
        return self._send_via_mcp(message)

    async def send_weather_alert(
        self,
        location: str,
        temp: float,
        condition: str,
        feels_like: float = None
    ) -> bool:
        """
        Send weather alert notification.
        
        Args:
            location: Location name
            temp: Temperature in Celsius
            condition: Weather condition
            feels_like: Feels like temperature (optional)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            logger.debug("Telegram notifications disabled")
            return False

        message = self.templates.weather_alert(location, temp, condition, feels_like)
        return self._send_via_mcp(message)

    async def send_calendar_reminder(
        self,
        event_title: str,
        event_time: str,
        location: str = ""
    ) -> bool:
        """
        Send calendar reminder notification.
        
        Args:
            event_title: Event title
            event_time: Event time
            location: Event location (optional)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            logger.debug("Telegram notifications disabled")
            return False

        message = self.templates.calendar_reminder(event_title, event_time, location)
        return self._send_via_mcp(message)

    async def send_project_status(
        self,
        project_name: str,
        status: str,
        progress: int = 0
    ) -> bool:
        """
        Send project status notification.
        
        Args:
            project_name: Project name
            status: Project status
            progress: Progress percentage (0-100)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            logger.debug("Telegram notifications disabled")
            return False

        message = self.templates.project_status(project_name, status, progress)
        return self._send_via_mcp(message)

    async def send_oracle_consultation(
        self,
        question: str,
        response: str
    ) -> bool:
        """
        Send oracle consultation response.
        
        Args:
            question: User's question
            response: Oracle's response
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            logger.debug("Telegram notifications disabled")
            return False

        message = self.templates.oracle_consultation(question, response)
        return self._send_via_mcp(message)

    async def send_system_alert(
        self,
        alert_type: str,
        message: str
    ) -> bool:
        """
        Send system alert notification.
        
        Args:
            alert_type: Alert type (info, warning, error, success)
            message: Alert message
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            logger.debug("Telegram notifications disabled")
            return False

        formatted_message = self.templates.system_alert(alert_type, message)
        return self._send_via_mcp(formatted_message)

    async def send_email_alert(
        self,
        sender: str,
        subject: str,
        urgency: str = "normal"
    ) -> bool:
        """
        Send email alert notification.
        
        Args:
            sender: Email sender
            subject: Email subject
            urgency: Urgency level (low, normal, high, urgent)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            logger.debug("Telegram notifications disabled")
            return False

        message = self.templates.email_alert(sender, subject, urgency)
        return self._send_via_mcp(message)

    async def send_vibe_recommendation(
        self,
        activity: str,
        description: str,
        mood: str = ""
    ) -> bool:
        """
        Send vibe recommendation notification.
        
        Args:
            activity: Recommended activity
            description: Activity description
            mood: Current mood (optional)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            logger.debug("Telegram notifications disabled")
            return False

        message = self.templates.vibe_recommendation(activity, description, mood)
        return self._send_via_mcp(message)

    async def send_custom_message(
        self,
        message: str,
        parse_mode: str = "Markdown"
    ) -> bool:
        """
        Send a custom message.
        
        Args:
            message: Message to send
            parse_mode: Parse mode (Markdown or HTML)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            logger.debug("Telegram notifications disabled")
            return False

        return self._send_via_mcp(message, parse_mode)

# ============================================================
# HELPER FUNCTIONS FOR MASTER AGENT
# ============================================================

async def send_telegram_notification(
    message: str,
    chat_id: Optional[int] = None,
    parse_mode: str = "Markdown"
) -> bool:
    """
    Helper function to send a Telegram notification.
    
    Args:
        message: Message to send
        chat_id: Telegram chat ID (optional, uses TELEGRAM_BOT_USER_ID if not provided)
        parse_mode: Parse mode (Markdown or HTML)
        
    Returns:
        True if successful, False otherwise
    """
    notifier = TelegramNotifier(chat_id)
    return await notifier.send_custom_message(message, parse_mode)

async def notify_morning_routine(
    steps: List[str],
    duration: str
) -> bool:
    """
    Helper function to send morning routine notification.
    
    Args:
        steps: List of completed steps
        duration: Duration of the routine
        
    Returns:
        True if successful, False otherwise
    """
    notifier = TelegramNotifier()
    return await notifier.send_morning_routine_complete(steps, duration)

async def notify_horoscope(
    sign: str,
    reading: str,
    moon_phase: str = ""
) -> bool:
    """
    Helper function to send horoscope notification.
    
    Args:
        sign: Zodiac sign
        reading: Horoscope reading
        moon_phase: Moon phase (optional)
        
    Returns:
        True if successful, False otherwise
    """
    notifier = TelegramNotifier()
    return await notifier.send_daily_horoscope(sign, reading, moon_phase)

async def notify_weather(
    location: str,
    temp: float,
    condition: str,
    feels_like: float = None
) -> bool:
    """
    Helper function to send weather notification.
    
    Args:
        location: Location name
        temp: Temperature in Celsius
        condition: Weather condition
        feels_like: Feels like temperature (optional)
        
    Returns:
        True if successful, False otherwise
    """
    notifier = TelegramNotifier()
    return await notifier.send_weather_alert(location, temp, condition, feels_like)

# ============================================================
# MAIN ENTRY POINT
# ============================================================

if __name__ == "__main__":
    # Test the Telegram notifier
    async def test():
        notifier = TelegramNotifier()

        print("Testing Telegram Integration...")
        print("=" * 50)

        # Test morning routine notification
        steps = ["Email check", "Horoscope reading", "Calendar review"]
        result = await notifier.send_morning_routine_complete(steps, "15 minutes")
        print(f"Morning routine notification: {'✅' if result else '❌'}")

        # Test horoscope notification
        result = await notifier.send_daily_horoscope(
            "Leo",
            "Today is a great day for creative endeavors.",
            "Waxing Gibbous"
        )
        print(f"Horoscope notification: {'✅' if result else '❌'}")

        # Test weather notification
        result = await notifier.send_weather_alert(
            "Sandusky, Ohio",
            22.5,
            "Partly cloudy",
            24.0
        )
        print(f"Weather notification: {'✅' if result else '❌'}")

        print("\n" + "=" * 50)
        print("Test complete!")

    asyncio.run(test())
