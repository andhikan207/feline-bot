import discord
from discord import app_commands
from discord.ext import commands, tasks
import logging
import os
import pytz
import requests
from datetime import datetime
from db_connect import get_user_data, update_timezone, add_reminder, get_reminders, remove_reminder

# Your Reminder Channel ID
REMINDER_CHANNEL_ID = 1339710713148604506  

# Setup logging to save errors in a file
LOG_DIR = "./bot_stuff/logs"
LOG_FILE = os.path.join(LOG_DIR, "reminders_logs.txt")

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

logging.basicConfig(filename=LOG_FILE, level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s")

def log_error(message):
    """Logs errors to the reminders log file."""
    logging.error(message)

class Reminder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_reminders.start()

    @app_commands.command(name="settimezone", description="Set your timezone (Auto-detects by default) ⏳")
    async def set_timezone(self, interaction: discord.Interaction, timezone: str):
        """Sets a user's timezone."""
        timezone = timezone.strip().title()  # Normalize case
        
        if timezone not in pytz.all_timezones:
            await interaction.response.send_message(
                "That timezone doesn't seem right! 🙀 Try something like `Asia/Jakarta` or `America/New_York`!\n"
                "🔗 [Click here for a timezone list!](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)",
                ephemeral=True
            )
            return

        update_timezone(interaction.user.id, timezone)
        await interaction.response.send_message(
            f"⏰ Your timezone is now set to `{timezone}`! I'll remind you in your local time!"
        )

    @app_commands.command(name="remind", description="Set a reminder with a date and time!")
    async def remind(self, interaction: discord.Interaction, task: str, frequency: str, year: int, month: int, day: int, hour: int, minute: int):
        """Creates a reminder and stores it in MongoDB."""
        try:
            user_data = get_user_data(interaction.user.id)
            user_tz_name = user_data.get("timezone", "UTC")
            user_tz = pytz.timezone(user_tz_name)

            reminder_datetime = datetime(year, month, day, hour, minute, 0)
            reminder_datetime = user_tz.localize(reminder_datetime)  # Convert to timezone-aware datetime

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

            add_reminder(interaction.user.id, reminder_data)

            embed = discord.Embed(
                title="🐱 Reminder Set!",
                description=f"I'll remind you about **{task}** on **{reminder_datetime.strftime('%Y-%m-%d %H:%M %Z')}**!",
                color=discord.Color.orange()
            )
            embed.set_footer(text="I'll notify you when it's time! ✨")

            await interaction.response.send_message(f"{interaction.user.mention}", embed=embed)

        except ValueError:
            await interaction.response.send_message("❌ That date/time format is incorrect. Use `YYYY MM DD HH MM`!", ephemeral=True)
            log_error(f"Invalid date/time format entered: {year}-{month}-{day} {hour}:{minute}")

    @tasks.loop(seconds=60)
    async def check_reminders(self):
        now_utc = datetime.now(pytz.utc)
        users = [user for user in get_reminders(None) if user["reminders"]]
        
        for user in users:
            user_id = user["_id"]
            reminders = user["reminders"]
            reminders_due = [r for r in reminders if now_utc >= r["time"].astimezone(pytz.utc)]
            
            for reminder in reminders_due:
                channel = self.bot.get_channel(REMINDER_CHANNEL_ID)

                if channel:
                    try:
                        user_obj = await self.bot.fetch_user(user_id)
                        await channel.send(f"{user_obj.mention}")

                        embed = discord.Embed(
                            title="🐱⏰ Reminder Time!",
                            description=f"Hey {user_obj.mention}, it's time to do **{reminder['task']}**!\n"
                                        "Please do it now! ✨",
                            color=discord.Color.red()
                        )
                        embed.set_footer(text=f"📅 {reminder['time'].strftime('%Y-%m-%d %H:%M %Z')}")

                        await channel.send(embed=embed)
                    
                    except Exception as e:
                        log_error(f"Could not fetch user: {e}")

                if reminder["frequency"] == "once":
                    remove_reminder(user_id, reminder["task"])

    @check_reminders.before_loop
    async def before_check_reminders(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(Reminder(bot))
