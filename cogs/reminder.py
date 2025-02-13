import discord
from discord import app_commands
from discord.ext import commands, tasks
import asyncio
from datetime import datetime, timedelta

class Reminder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.reminders = []  # Stores all active reminders
        self.check_reminders.start()  # Starts the loop when the bot is online

    @app_commands.command(name="remind", description="Set a reminder")
    async def remind(self, interaction: discord.Interaction, task: str, frequency: str, time: str):
        """Slash Command: /remind <task> <everyday or once> <HH:MM>
        Example: /remind "Check in to my shift" everyday 09:00
        """
        try:
            # Convert time input to a datetime object
            reminder_time = datetime.strptime(time, "%H:%M").time()
            
            # Store the reminder
            self.reminders.append({"task": task, "frequency": frequency, "time": reminder_time, "channel": interaction.channel})
            
            await interaction.response.send_message(f"✅ Reminder set: **{task}** at **{time}** ({frequency}).")
        except ValueError:
            await interaction.response.send_message("❌ Invalid time format. Please use HH:MM (24-hour format).", ephemeral=True)

    @tasks.loop(seconds=60)  # Runs every minute
    async def check_reminders(self):
        """Loop that checks every minute if a reminder should be triggered."""
        now = datetime.now().time()

        for reminder in self.reminders:
            if now.hour == reminder["time"].hour and now.minute == reminder["time"].minute:
                await reminder["channel"].send(f"⏰ Reminder: {reminder['task']}")

                # Remove if it's a one-time reminder
                if reminder["frequency"].lower() == "once":
                    self.reminders.remove(reminder)

    @check_reminders.before_loop
    async def before_check_reminders(self):
        await self.bot.wait_until_ready()  # Wait until bot is fully ready before starting the loop

# Required function for cogs
async def setup(bot):
    await bot.add_cog(Reminder(bot))
