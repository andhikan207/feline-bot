import discord
from discord.ext import commands
import asyncio
import os

# Import MongoDB connection (ensures it's initialized at startup)
from db_connect import client

# Function to retrieve bot token from Google Secret Manager
from google.cloud import secretmanager

async def get_secret(secret_id, retries=3, delay=5):
    """Retrieve a secret from Google Secret Manager with retries."""
    client = secretmanager.SecretManagerServiceClient()
    secret_name = f"projects/feline-bot-discord/secrets/{secret_id}/versions/latest"

    for attempt in range(retries):
        try:
            response = client.access_secret_version(request={"name": secret_name})
            return response.payload.data.decode("UTF-8")
        except Exception as e:
            print(f"❌ Error retrieving secret (attempt {attempt+1}): {e}")
            if attempt < retries - 1:
                await asyncio.sleep(delay)  # Proper async delay
            else:
                print("🚨 Failed to retrieve secret after multiple attempts. Exiting.")
                return None

# Retrieve bot token securely
TOKEN = asyncio.run(get_secret("bot-token"))
if not TOKEN:
    raise RuntimeError("❌ Bot token could not be retrieved! Check Google Secret Manager.")

# Enable intents
intents = discord.Intents.default()
intents.message_content = True

# Initialize bot with a command prefix
bot = commands.Bot(command_prefix="/", intents=intents)

@bot.event
async def on_ready():
    """Triggered when the bot is ready."""
    print(f"✅ Logged in as {bot.user}")
    
    try:
        synced = await bot.tree.sync()  # Syncs slash commands globally
        print(f"✅ Synced {len(synced)} slash commands.")
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")

# Get absolute path to cogs directory
COGS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cogs")

async def load_cogs():
    """Dynamically loads all cogs from the 'cogs' folder."""
    if not os.path.exists(COGS_DIR):
        print(f"❌ Cogs directory not found: {COGS_DIR}")
        return

    for filename in os.listdir(COGS_DIR):
        if filename.endswith(".py") and filename != "__init__.py":
            cog_name = f"cogs.{filename[:-3]}"
            try:
                await bot.load_extension(cog_name)
                print(f"✅ Loaded cog: {cog_name}")
            except Exception as e:
                print(f"❌ Failed to load {cog_name}: {e}")

async def main():
    """Main entry point for running the bot."""
    async with bot:
        await load_cogs()  # Load all cogs before starting the bot
        await bot.start(TOKEN, reconnect=True)

asyncio.run(main())
