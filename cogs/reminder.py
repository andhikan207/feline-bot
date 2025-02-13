import discord
from discord import app_commands
from discord.ext import commands, tasks
import asyncio
import requests
import os
import logging
from datetime import datetime
import pytz

# Your Reminder Channel ID
REMINDER_CHANNEL_ID = 1339710713148604506  

# Default Timezone (UTC Fallback)
DEFAULT_TZ = pytz.utc

# Store user timezones (temporary, ideally use a database)
user_timezones = {}

# Setup logging to save errors in a file
LOG_DIR = "./bot_stuff/logs"
LOG_FILE = os.path.join(LOG_DIR, "reminders_logs.txt")

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

logging.basicConfig(filename=LOG_FILE, level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s")

def log_error(message):
    """Logs errors to the reminders log file."""
    logging.error(message)

def get_user_timezone():
    """Auto-detects the user's timezone based on their IP using WorldTimeAPI."""
    try:
        response = requests.get("http://worldtimeapi.org/api/ip")
        data = response.json()
        return data["timezone"]
    except Exception as e:
        log_error(f"Could not fetch timezone: {e}")
        return "UTC"

class Reminder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.reminders = []
        self.check_reminders.start()

    @app_commands.command(name="settimezone", description="Manually set your timezone (Auto-detects by default) ⏳")
    async def set_timezone(self, interaction: discord.Interaction, timezone: str):
        """Manually sets a user's timezone."""
        if timezone not in pytz.all_timezones:
            await interaction.response.send_message(
                "😥 Oopsie! That timezone doesn't seem right! Try something like `Asia/Jakarta` or `America/New_York`! 🌏\n"
                "🔗 [Click here for a timezone list!](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)",
                ephemeral=True
            )
            return

        user_timezones[interaction.user.id] = timezone
        await interaction.response.send_message(
            f"Your timezone is now set to `{timezone}`! I'll remind you in your local time! ⏰"
        )

    @app_commands.command(name="remind", description="Set a super cute reminder! ✨")
    async def remind(self, interaction: discord.Interaction, task: str, frequency: str, time: str):
        """Creates a reminder with an automatically detected timezone."""
        try:
            user_tz_name = user_timezones.get(interaction.user.id, get_user_timezone())
            user_tz = pytz.timezone(user_tz_name)

            reminder_time = datetime.strptime(time, "%H:%M").time()
            reminder_datetime = datetime.now(user_tz).replace(
                hour=reminder_time.hour, 
                minute=reminder_time.minute, 
                second=0, 
                microsecond=0
            )

            if frequency.lower() not in ["once", "daily"]:
                await interaction.response.send_message("❌ Use `once` or `daily` for the reminder frequency!", ephemeral=True)
                return

            reminder_data = {
                "task": task,
                "frequency": frequency.lower(),
                "time": reminder_datetime,
                "user_id": interaction.user.id,
                "timezone": user_tz_name,
            }

            self.reminders.append(reminder_data)
            print(f"✅ [DEBUG] Reminder scheduled: {reminder_data}")

            await interaction.response.send_message(
                f"Okay! I'll remind you about **{task}** at **{reminder_datetime.strftime('%H:%M %Z')}** ({frequency})!\n"
                f"🌍 I detected your timezone as `{user_tz_name}`."
            )

        except ValueError:
            await interaction.response.send_message("❌ That time format is incorrect. Use `HH:MM` (24-hour format)!", ephemeral=True)
            log_error(f"Invalid time format entered: {time}")

    @tasks.loop(seconds=60)
    async def check_reminders(self):
        now_utc = datetime.now(pytz.utc)
        print(f"🔍 [DEBUG] Checking reminders at {now_utc.strftime('%H:%M %Z')}")

        for reminder in self.reminders:
            reminder_time_utc = reminder["time"].astimezone(pytz.utc)

            if now_utc.hour == reminder_time_utc.hour and now_utc.minute == reminder_time_utc.minute:
                channel = self.bot.get_channel(REMINDER_CHANNEL_ID)

                if channel:
                    try:
                        user = await self.bot.fetch_user(reminder["user_id"])
                        await channel.send(
                            f"**Hey, {user.mention}!**! It's time for: **{reminder['task']}**! ⏰\n"
                            f"Please do it now! 😺"
                        )
                        print(f"📢 [DEBUG] Reminder sent to {channel.name}")

                    except Exception as e:
                        log_error(f"Could not fetch user: {e}")

                if reminder["frequency"] == "once":
                    self.reminders.remove(reminder)
                    print(f"🗑️ [DEBUG] Removed one-time reminder: {reminder}")

    @check_reminders.before_loop
    async def before_check_reminders(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(Reminder(bot))
