import discord
from discord import app_commands
from discord.ext import commands, tasks
import logging
import os
import pytz
import requests
from datetime import datetime

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

        user_timezones[interaction.user.id] = timezone
        await interaction.response.send_message(
            f"⏰ Your timezone is now set to `{timezone}`! I'll remind you in your local time!"
        )

    @app_commands.command(name="remind", description="Set a reminder with a date and time!")
    async def remind(self, interaction: discord.Interaction, task: str, frequency: str, year: int, month: int, day: int, hour: int, minute: int):
        """Creates a reminder with an automatically detected timezone and structured time input."""
        try:
            user_tz_name = user_timezones.get(interaction.user.id, get_user_timezone())
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

            self.reminders.append(reminder_data)
            print(f"✅ [DEBUG] Reminder scheduled: {reminder_data}")

            # 🌟 Combine Mention and Embed into One Message
            embed = discord.Embed(
                title="🐱 Reminder Set!",
                description=f"I'll remind you about **{task}** on **{reminder_datetime.strftime('%Y-%m-%d %H:%M %Z')}**!",
                color=discord.Color.orange()
            )
            embed.add_field(name="📅 Date", value=f"**{reminder_datetime.strftime('%Y-%m-%d')}**", inline=True)
            embed.add_field(name="⏰ Time", value=f"**{reminder_datetime.strftime('%H:%M %Z')}**", inline=True)
            embed.add_field(name="🔁 Frequency", value=f"**{frequency.capitalize()}**", inline=True)
            embed.set_footer(text="I'll notify you when it's time! ✨")

            # 🌟 Send as a SINGLE message to avoid "double chatting"
            await interaction.response.send_message(f"{interaction.user.mention}", embed=embed)

        except ValueError:
            await interaction.response.send_message("❌ That date/time format is incorrect. Use `YYYY MM DD HH MM`!", ephemeral=True)
            log_error(f"Invalid date/time format entered: {year}-{month}-{day} {hour}:{minute}")

    @tasks.loop(seconds=60)
    async def check_reminders(self):
        now_utc = datetime.now(pytz.utc)

        # ⬇ Reduce debug log spam, show logs only if there's a match
        reminders_due = [r for r in self.reminders if now_utc >= r["time"].astimezone(pytz.utc)]
        if reminders_due:
            print(f"🔍 [DEBUG] Checking reminders at {now_utc.strftime('%Y-%m-%d %H:%M %Z')} - Found {len(reminders_due)} reminders!")

        for reminder in reminders_due:
            channel = self.bot.get_channel(REMINDER_CHANNEL_ID)

            if channel:
                try:
                    user = await self.bot.fetch_user(reminder["user_id"])

                    # 🌟 First, send a mention so Discord will actually notify the user
                    await channel.send(f"{user.mention}")

                    # 🌟 Then, send an embed with the structured reminder details
                    embed = discord.Embed(
                        title="🐱⏰ Reminder Time!",
                        color=discord.Color.red()
                    )
                    embed.description = (
                        f"Hey {user.mention}, it's time to do **{reminder['task']}**!\n"
                        f"Please do it now! ✨"
                    )
                    embed.set_footer(text=f"📅 {reminder['time'].strftime('%Y-%m-%d %H:%M %Z')}")

                    await channel.send(embed=embed)
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
