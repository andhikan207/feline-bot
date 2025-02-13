import discord
from discord.ext import commands
import asyncio
import os

# Function to retrieve bot token from Google Secret Manager
from google.cloud import secretmanager

def get_secret(secret_id, retries=3, delay=5):
    client = secretmanager.SecretManagerServiceClient()
    secret_name = f"projects/feline-bot-discord/secrets/{secret_id}/versions/latest"

    for attempt in range(retries):
        try:
            response = client.access_secret_version(request={"name": secret_name})
            return response.payload.data.decode("UTF-8")
        except Exception as e:
            print(f"Error retrieving secret (attempt {attempt+1}): {e}")
            if attempt < retries - 1:
                asyncio.sleep(delay)
            else:
                raise RuntimeError("Failed to retrieve secret after multiple attempts.")

# Retrieve bot token securely
TOKEN = get_secret("bot-token")

# Enable intents
intents = discord.Intents.default()
intents.message_content = True

# Initialize the bot
bot = commands.Bot(command_prefix="/", intents=intents)

# Load cogs (commands from other files)
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

# Dynamically load all cogs from 'cogs' folder
async def load_cogs():
    for filename in os.listdir("./bot_files/cogs"):
        if filename.endswith(".py") and filename != "__init__.py":
            await bot.load_extension(f"cogs.{filename[:-3]}")

# Run bot
async def main():
    async with bot:
        await load_cogs()  # Load all cogs (commands)
        await bot.start(TOKEN, reconnect=True)

asyncio.run(main())
