import discord
from discord.ext import commands

class Poke(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name = "poke", description = "Pokes feline.")
    async def slash_poke(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"Pokes {interaction.user.mention} back!")
    
async def setup(bot):
    await bot.add_cog(Poke(bot))