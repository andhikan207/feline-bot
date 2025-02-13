import discord
from discord.ext import commands
from google.cloud import secretmanager
import asyncio

# Function to get the secret from Secret Manager with retry logic
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
                asyncio.sleep(delay)  # Wait before retrying
            else:
                raise RuntimeError("Failed to retrieve secret after multiple attempts.")

# Retrieve bot token securely from Secret Manager
TOKEN = get_secret("bot-token")

# Enable intents for message content
intents = discord.Intents.default()
intents.message_content = True  # Enable message content intent

# Create the bot instance and pass the intents
bot = commands.Bot(command_prefix="/", intents=intents)

# Event for when the bot is ready
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

# Event for handling disconnections
@bot.event
async def on_disconnect():
    print("⚠️ Disconnected from Discord. Attempting to reconnect...")

# Event for handling errors and automatic reconnections
@bot.event
async def on_error(event, *args, **kwargs):
    print(f"❌ An error occurred: {event}. Reconnecting in 5 seconds...")
    await asyncio.sleep(5)  # Wait before reconnecting
    await bot.connect(reconnect=True)

# Simple hello command
@bot.command()
async def hello(ctx):
    await ctx.send(f"Hello {ctx.author.mention}!")

# Run the bot with automatic reconnection enabled
bot.run(TOKEN, reconnect=True)
