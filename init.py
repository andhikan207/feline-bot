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

# Event when bot is ready
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

# Get absolute path to cogs directory
COGS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cogs")

# Debugging print statements
print(f"Checking if cogs folder exists at: {COGS_DIR}")

# Dynamically load all cogs from 'cogs' folder
async def load_cogs():
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

# Run bot
async def main():
    async with bot:
        await load_cogs()  # Load all cogs (commands)
        await bot.start(TOKEN, reconnect=True)

asyncio.run(main())
