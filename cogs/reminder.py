from discord.ext import commands, tasks
from datetime import datetime, timedelta

class Reminder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.reminders = []  # Stores all active reminders
        self.check_reminders.start()  # Starts the loop when the bot is online

    @commands.command()
    async def remind(self, ctx, task: str, frequency: str, time: str):
        try:
            # Convert time input to a datetime object
            reminder_time = datetime.strptime(time, "%H:%M").time()
            
            # Store the reminder
            self.reminders.append({"task": task, "frequency": frequency, "time": reminder_time, "channel": ctx.channel})
            
            await ctx.send(f"✅ Reminder set: **{task}** at **{time}** ({frequency}).")
        except ValueError:
            await ctx.send("❌ Invalid time format. Please use HH:MM (24-hour format).")

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
