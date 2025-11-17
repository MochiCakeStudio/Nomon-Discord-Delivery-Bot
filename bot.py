import discord
from discord.ext import commands
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('DISCORD_BOT_TOKEN')
bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
STATUS_FILE = os.path.join(SCRIPT_DIR, "status.txt")

def load_status():
    with open(STATUS_FILE, "r") as f:
        return f.read().strip()

@bot.event
async def on_ready():
    print(f"{bot.user.name} has awakened and is ready to go! ☁️꒰ঌ( •ө• )໒꒱")
    try:
        # Add current directory to path to find cogs
        import sys
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)

        # Add parent directory to path to find cogs in ../cogs
        parent_dir = os.path.dirname(current_dir)
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)

        await bot.load_extension('cogs.dev_cog')
        print("Dev cog loaded successfully.")
        await bot.load_extension('cogs.mail_cog')
        print("Mail cog loaded successfully.")

        await bot.load_extension('cogs.clear_cog')
        print("Clear cog loaded successfully.")
        await bot.load_extension('cogs.help_cog')
        print("Help cog loaded successfully.")
        await bot.load_extension('cogs.forum_bump_cog')
        print("Forum bump cog loaded successfully.")
        await bot.load_extension('cogs.logging_cog')
        print("Logging cog loaded successfully.")
        await bot.load_extension('cogs.embed_cog')
        print("Embed cog loaded successfully.")
        await bot.load_extension('dev_commands')
        print("Dev commands cog loaded successfully.")
        status = load_status()
        await bot.change_presence(activity=discord.Game(name=status))
        await bot.tree.sync()
        synced_commands = [cmd.name for cmd in bot.tree.get_commands()]
        print(f"Slash commands synced globally successfully. Synced commands: {synced_commands}")
    except Exception as e:
        print(f"Failed to load cogs or sync commands: {e}")





bot.run(TOKEN)
