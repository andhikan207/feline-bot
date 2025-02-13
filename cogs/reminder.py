import discord
from discord import app_commands
from discord.ext import commands, tasks
import asyncio
from datetime import datetime, timedelta

# Set your desired reminder channel ID (Replace this with the actual channel ID)
REMINDER_CHANNEL_ID = 1339710713148604506  # Replace with your channel's ID

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
                "user": interaction.user.mention,  # Tag the user
            }

            self.reminders.append(reminder_data)
            await interaction.response.send_message(
                f"✅ Reminder set: **{task}** at **{time}** ({frequency}).\n"
                f"⏰ **Reminders will always be sent in <#{REMINDER_CHANNEL_ID}>.**"
            )
        except ValueError:
            await interaction.response.send_message(
                "❌ Invalid time format! Use HH:MM (24-hour format).", ephemeral=True
            )

    @tasks.loop(seconds=60)  # Runs every minute
    async def check_reminders(self):
        now = datetime.now().time()
        for reminder in self.reminders:
            if now.hour == reminder["time"].hour and now.minute == reminder["time"].minute:
                channel = self.bot.get_channel(REMINDER_CHANNEL_ID)

                if channel:
                    await channel.send(
                        f"⏰ **Hello, {reminder['user']}**! Have you {reminder['task']} yet?"
                    )
                else:
                    print(f"❌ ERROR: Could not find channel ID {REMINDER_CHANNEL_ID}")

                if reminder["frequency"] == "once":
                    self.reminders.remove(reminder)

    @check_reminders.before_loop
    async def before_check_reminders(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(Reminder(bot))
