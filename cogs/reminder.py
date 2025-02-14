import discord
from discord import app_commands
from discord.ext import commands, tasks
import logging
import os
import pytz
from datetime import datetime, timedelta
from db_connect import get_user_data, update_timezone, add_reminder, get_reminders, remove_reminder

# Your Reminder Channel ID
REMINDER_CHANNEL_ID = 1339710713148604506  

# Setup logging directories
LOG_DIR = "./bot_stuff/logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Error logging
ERROR_LOG_FILE = os.path.join(LOG_DIR, "reminders_errors.txt")
logging.basicConfig(filename=ERROR_LOG_FILE, level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s")

# Debug logging
DEBUG_LOG_FILE = os.path.join(LOG_DIR, "debug_logs.txt")

def log_error(message):
    """Logs errors to the reminders log file."""
    logging.error(message)

def log_debug(message):
    """Logs debug info to track executions."""
    with open(DEBUG_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")

class Reminder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_reminders.start()
        log_debug("✅ Reminder cog initialized.")

    @app_commands.command(name="settimezone", description="Set your timezone (Auto-detects by default) ⏳")
    async def set_timezone(self, interaction: discord.Interaction, timezone: str):
        """Sets a user's timezone (ignores case)."""
        timezone = timezone.strip().title()

        if timezone not in pytz.all_timezones:
            await interaction.response.send_message(
                "🙀 That timezone doesn't seem right! Try `Asia/Jakarta` or `America/New_York`!\n"
                "🔗 [Click here for a timezone list!](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)",
                ephemeral=True
            )
            return

        update_timezone(interaction.user.id, timezone)
        log_debug(f"🌍 Updated timezone for {interaction.user.id} -> {timezone}")

        await interaction.response.send_message(
            f"⏰ Your timezone is now set to `{timezone}`! I'll remind you in your local time!"
        )

    @app_commands.command(name="remind", description="Set a reminder with a date and time! 📅⏰")
    async def remind(self, interaction: discord.Interaction, task: str, frequency: str, year: int = None, month: int = None, day: int = None, hour: int = None, minute: int = None):
        """Creates a reminder and stores it in MongoDB with UTC time."""
        try:
            user_data = get_user_data(interaction.user.id)
            user_tz_name = user_data.get("timezone", "UTC")
            user_tz = pytz.timezone(user_tz_name)

            if frequency.lower() == "daily":
                # If it's a daily reminder, only store time and set the next occurrence
                now_local = datetime.now(user_tz)
                reminder_datetime = user_tz.localize(datetime(now_local.year, now_local.month, now_local.day, hour, minute, 0))
                if reminder_datetime < now_local:
                    reminder_datetime += timedelta(days=1)  # Set for the next day if the time has passed
            else:
                # Convert user input to a timezone-aware datetime
                reminder_datetime = user_tz.localize(datetime(year, month, day, hour, minute, 0))

            # Convert to UTC before storing
            reminder_utc = reminder_datetime.astimezone(pytz.utc)

            if frequency.lower() not in ["once", "daily"]:
                await interaction.response.send_message("❌ Use `once` or `daily` for the reminder frequency!", ephemeral=True)
                return

            reminder_data = {
                "task": task,
                "frequency": frequency.lower(),
                "time": reminder_utc.isoformat(),  # Store in UTC as ISO format
                "user_id": interaction.user.id,
                "timezone": user_tz_name,
            }

            add_reminder(interaction.user.id, reminder_data)
            log_debug(f"📌 Reminder set for {interaction.user.id}: {reminder_data}")

            # Embed message
            embed = discord.Embed(
                title="🐱 Reminder Set!",
                description=f"I'll remind you about **{task}**!",
                color=discord.Color.orange()
            )
            embed.add_field(name="📅 Date", value=f"**{reminder_datetime.strftime('%Y-%m-%d')}**", inline=True)
            embed.add_field(name="⏰ Time", value=f"**{reminder_datetime.strftime('%H:%M %Z')}**", inline=True)
            embed.add_field(name="🔁 Frequency", value=f"**{frequency.capitalize()}**", inline=True)
            embed.set_footer(text="I'll notify you when it's time! ✨")

            await interaction.response.send_message(f"{interaction.user.mention}", embed=embed)

        except ValueError:
            await interaction.response.send_message("❌ That date/time format is incorrect. Use `YYYY MM DD HH MM`!", ephemeral=True)
            log_error(f"⚠️ Invalid date/time format entered by {interaction.user.id}: {year}-{month}-{day} {hour}:{minute}")

    @tasks.loop(seconds=60)
    async def check_reminders(self):
        """Checks reminders every minute and sends notifications if needed."""
        now_utc = datetime.now(pytz.utc)  # Get current time in UTC
        log_debug(f"🔍 Checking reminders at {now_utc.strftime('%Y-%m-%d %H:%M %Z')}")

        users_with_reminders = get_reminders(None)

        for user in users_with_reminders:
            user_id = user["_id"]
            reminders = user["reminders"]

            for reminder in reminders:
                reminder_time_utc = datetime.fromisoformat(reminder["time"])

                if now_utc >= reminder_time_utc:
                    channel = self.bot.get_channel(REMINDER_CHANNEL_ID)
                    if channel:
                        try:
                            user_obj = await self.bot.fetch_user(user_id)
                            await channel.send(f"{user_obj.mention}")

                            embed = discord.Embed(
                                title="🐱⏰ Reminder Time!",
                                description=f"Hey {user_obj.mention}, it's time to do **{reminder['task']}**!",
                                color=discord.Color.red()
                            )
                            embed.set_footer(text=f"📅 {reminder_time_utc.strftime('%Y-%m-%d %H:%M %Z')}")

                            await channel.send(embed=embed)
                            log_debug(f"📢 Reminder sent to {user_id}: {reminder}")
                        except Exception as e:
                            log_error(f"⚠️ Could not fetch user {user_id}: {e}")
                    if reminder["frequency"] == "once":
                        remove_reminder(user_id, reminder["task"])

    @check_reminders.before_loop
    async def before_check_reminders(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(Reminder(bot))
    log_debug("✅ Reminder cog loaded successfully.")
