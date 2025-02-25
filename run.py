import os
import asyncio
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

#Load env vars
load_dotenv()

AUTHTKN = os.getenv("AUTH_TKN")

# Intents & load slash command feature...
intents = discord.Intents.default()
bot = commands.Bot(command_prefix = "/", intents = intents)

# Load all modules.
async def load_modules():
    for filename in os.listdir("./module"):
        if filename.endswith(".py"):
            await bot.load_extension(f"module.{filename[:-3]}")

# -[RUN]-
# # When online....
@bot.event
async def on_ready():
    print(f"🚀 Logged in as {bot.user}")
    
async def main():
    await load_modules()
    async with bot:
        await bot.start(AUTHTKN)
        try:
            synced = await bot.tree.sync()
            print(f"✅ Synced {len(synced)} command(s)")
        except Exception as e:
            print(f"❌ Error syncing commands: {e}")

asyncio.run(main())