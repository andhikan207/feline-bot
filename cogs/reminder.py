import discord
from discord import app_commands
from discord.ext import commands, tasks
import asyncio
from datetime import datetime

# Set your desired reminder channel ID (Replace this with your actual server channel ID)
REMINDER_CHANNEL_ID = 1339710713148604506  # Update with your actual channel ID

class Reminder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.reminders = []  # Stores all active reminders
        self.check_reminders.start()  # Start checking reminders

    @app_commands.command(name="remind", description="Set a reminder")
    async def remind(
        self, 
        interaction: discord.Interaction, 
        task: str, 
        frequency: str, 
        time: str
    ):
        """
        Slash Command: /remind <task> <once/daily> <HH:MM>
        Example:
        - `/remind "Check-in to work" daily 09:00`
        - `/remind "Drink water" once 14:30`
        """

        try:
            reminder_time = datetime.strptime(time, "%H:%M").time()

            if frequency.lower() not in ["once", "daily"]:
                await interaction.response.send_message(
                    "❌ Invalid frequency! Use `once` or `daily`.", ephemeral=True
                )
                return

            reminder_data = {
                "task": task,
                "frequency": frequency.lower(),
                "time": reminder_time,
                "user_id": interaction.user.id,  # Store user ID to mention later
            }

            self.reminders.append(reminder_data)

            print(f"✅ [DEBUG] Reminder scheduled: {reminder_data}")  # DEBUG LOG

            await interaction.response.send_message(
                f"✅ **Reminder set:** **{task}** at **{time}** ({frequency}).\n"
                f"⏰ **Reminders will always be sent in** <#{REMINDER_CHANNEL_ID}>."
            )

        except ValueError:
            await interaction.response.send_message(
                "❌ Invalid time format! Use HH:MM (24-hour format).", ephemeral=True
            )

    @tasks.loop(seconds=60)  # Runs every minute
    async def check_reminders(self):
        now = datetime.now().time()
        print(f"🔍 [DEBUG] Checking reminders at {now.strftime('%H:%M')}")  # DEBUG LOG

        for reminder in self.reminders:
            if now.hour == reminder["time"].hour and now.minute == reminder["time"].minute:
                channel = self.bot.get_channel(REMINDER_CHANNEL_ID)

                if channel:
                    try:
                        user = await self.bot.fetch_user(reminder["user_id"])  # Fetch user by ID
                        print(f"👤 [DEBUG] Fetching user: {user}")  # DEBUG LOG

                        await channel.send(
                            f"⏰ **Reminder for {user.mention}**: {reminder['task']}"
                        )
                        print(f"📢 [DEBUG] Reminder sent to {channel.name}")  # DEBUG LOG

                    except Exception as e:
                        print(f"❌ [ERROR] Could not fetch user: {e}")  # DEBUG LOG

                else:
                    print(f"❌ [ERROR] Could not find channel ID {REMINDER_CHANNEL_ID}")  # DEBUG LOG

                if reminder["frequency"] == "once":
                    self.reminders.remove(reminder)
                    print(f"🗑️ [DEBUG] Removed one-time reminder: {reminder}")  # DEBUG LOG

    @check_reminders.before_loop
    async def before_check_reminders(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(Reminder(bot))
