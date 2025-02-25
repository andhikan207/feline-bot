import os
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

# When online....
@bot.event
async def on_ready():
    print(f"🚀 Logged in as {bot.user}")
    try:
        synced = await tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Error syncing commands: {e}")

# Load all modules.
for filename in os.listdir("./module"):
    if filename.endswith(".py"):
        bot.load_extension(f"module.{filename[:-3]}")

bot.run(AUTHTKN)