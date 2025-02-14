import discord
from discord import app_commands
from discord.ext import commands, tasks
import logging
import os
import pytz
from datetime import datetime
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
    with open(ERROR_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - ERROR: {message}\n")

def log_debug(message):
    """Logs debug info to track executions."""
    with open(DEBUG_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - DEBUG: {message}\n")

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
    async def remind(self, interaction: discord.Interaction, task: str, frequency: str, hour: int, minute: int, year: int = None, month: int = None, day: int = None):
        """Creates a reminder and stores it in MongoDB with UTC time."""
        try:
            user_data = get_user_data(interaction.user.id)
            user_tz_name = user_data.get("timezone", "UTC")
            user_tz = pytz.timezone(user_tz_name)

            if frequency.lower() == "daily":
                # If daily, we only store time (ignore date)
                reminder_datetime = user_tz.localize(datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0))
            else:
                # If one-time, require full date
                if not year or not month or not day:
                    await interaction.response.send_message("❌ For one-time reminders, you must provide a full date!", ephemeral=True)
                    return
                reminder_datetime = user_tz.localize(datetime(year, month, day, hour, minute, 0))

            # Convert to UTC before storing
            reminder_utc = reminder_datetime.astimezone(pytz.utc)

            reminder_data = {
                "task": task,
                "frequency": frequency.lower(),
                "time": reminder_utc.isoformat(),  # Store as ISO format string
                "user_id": interaction.user.id,
                "timezone": user_tz_name,
            }

            add_reminder(interaction.user.id, reminder_data)
            log_debug(f"📌 Reminder set for {interaction.user.id}: {reminder_data}")

            # Embed message
            embed = discord.Embed(
                title="🐱 Reminder Set!",
                description=f"I'll remind you about **{task}** at **{reminder_datetime.strftime('%H:%M %Z')}**!",
                color=discord.Color.orange()
            )
            if frequency.lower() == "once":
                embed.add_field(name="📅 Date", value=f"**{reminder_datetime.strftime('%Y-%m-%d')}**", inline=True)
            embed.add_field(name="⏰ Time", value=f"**{reminder_datetime.strftime('%H:%M %Z')}**", inline=True)
            embed.add_field(name="🔁 Frequency", value=f"**{frequency.capitalize()}**", inline=True)
            embed.set_footer(text="I'll notify you when it's time! ✨")

            await interaction.response.send_message(f"{interaction.user.mention}", embed=embed)

        except ValueError:
            await interaction.response.send_message("❌ That date/time format is incorrect!", ephemeral=True)
            log_error(f"⚠️ Invalid date/time format entered by {interaction.user.id}: {hour}:{minute}, {year}-{month}-{day}")

    @tasks.loop(seconds=60)
    async def check_reminders(self):
        """Checks reminders every minute and sends notifications if needed."""
        now_utc = datetime.now(pytz.utc)
        log_debug(f"🔍 Checking reminders at {now_utc.strftime('%Y-%m-%d %H:%M %Z')}")

        users_with_reminders = get_reminders(None)

        for user in users_with_reminders:
            user_id = user["_id"]
            reminders = user["reminders"]

            for reminder in reminders:
                reminder_time_utc = datetime.fromisoformat(reminder["time"])
                user_tz = pytz.timezone(reminder["timezone"])
                reminder_local_time = reminder_time_utc.astimezone(user_tz)

                log_debug(f"🕒 Checking reminder: {user_id} -> {reminder['task']} | Reminder Time: {reminder_local_time.strftime('%Y-%m-%d %H:%M %Z')}")

                if reminder["frequency"] == "daily":
                    now_local = datetime.now(user_tz)
                    if now_local.hour == reminder_local_time.hour and now_local.minute == reminder_local_time.minute:
                        await self.send_reminder(user_id, reminder)
                elif now_utc >= reminder_time_utc:
                    await self.send_reminder(user_id, reminder)
                    if reminder["frequency"] == "once":
                        remove_reminder(user_id, reminder["task"])
                        log_debug(f"🗑️ Removed one-time reminder for {user_id}: {reminder['task']}")

    async def send_reminder(self, user_id, reminder):
        """Helper function to send reminders."""
        channel = self.bot.get_channel(REMINDER_CHANNEL_ID)
        if channel:
            user_obj = await self.bot.fetch_user(user_id)
            await channel.send(f"{user_obj.mention}")

            embed = discord.Embed(
                title="🐱⏰ Reminder Time!",
                description=f"Hey {user_obj.mention}, it's time to do **{reminder['task']}**!\nPlease do it now! ✨",
                color=discord.Color.red()
            )
            embed.set_footer(text=f"📅 {reminder['time']}")
            await channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Reminder(bot))
    log_debug("✅ Reminder cog loaded successfully.")
