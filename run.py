import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

#load env vars
load_dotenv()

AUTHTKN = os.getenv("AUTH_TKN")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix = "!", intents = intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

bot.run(AUTHTKN)