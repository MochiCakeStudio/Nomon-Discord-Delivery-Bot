import sys
sys.path.append('..')
import discord
from discord.ext import commands
import asyncio

async def test():
    bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())
    try:
        await bot.load_extension('cogs.embed_cog')
        print("Embed cog loaded successfully.")
    except Exception as e:
        print(f"Failed to load embed cog: {e}")

asyncio.run(test())
