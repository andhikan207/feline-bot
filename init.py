import discord
from discord.ext import commands
from google.cloud import secretmanager

# Function to get the secret from Secret Manager
def get_secret(secret_id):
    client = secretmanager.SecretManagerServiceClient()
    secret_name = f"projects/feline-bot-discord/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": secret_name})
    return response.payload.data.decode("UTF-8")

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
    print(f"Logged in as {bot.user}")

# Simple hello command
@bot.command()
async def hello(ctx):
    await ctx.send(f"Hello {ctx.author.mention}!")

# Run the bot with the retrieved token
bot.run(TOKEN)
