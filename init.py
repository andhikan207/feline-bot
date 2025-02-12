import discord
from discord.ext import commands

import auth  # Import the auth file

# Use the auth from auth.py
bot_auth = auth.auth_token

# Enable intents
intents = discord.Intents.default()
intents.message_content = True  # Enable message content intent

# Pass intents to bot
bot = commands.Bot(command_prefix = "/", intents = intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.command()
async def hello(ctx):
    await ctx.send(f"Hello {ctx.author.mention}!")

bot.run(bot_auth)