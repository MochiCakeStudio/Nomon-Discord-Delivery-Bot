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
SERVERS_FILE = os.path.join(SCRIPT_DIR, "servers.txt")
ADS_FILE = os.path.join(SCRIPT_DIR, "ads.txt")
STATUS_FILE = os.path.join(SCRIPT_DIR, "status.txt")

def load_servers():
    with open(SERVERS_FILE, "r") as f:
        return [int(line.strip()) for line in f if line.strip()]

def load_ads():
    with open(ADS_FILE, "r") as f:
        content = f.read().strip()
        return content.split("\n\n")  # ads separated by blank lines

def load_status():
    with open(STATUS_FILE, "r") as f:
        return f.read().strip()

@bot.event
async def on_ready():
    print(f"{bot.user.name} has awakened and is ready to go! ☁️꒰ঌ( •ө• )໒꒱")
    try:
        # Add parent directory to path to find cogs
        import sys
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        
        await bot.load_extension('cogs.embed_cog')
        print("Embed cog loaded successfully.")
        await bot.load_extension('cogs.logging_cog')
        print("Logging cog loaded successfully.")
        await bot.load_extension('cogs.server_messages_cog')
        print("Server messages cog loaded successfully.")
        await bot.load_extension('cogs.dev_cog')
        print("Dev cog loaded successfully.")
        await bot.load_extension('cogs.mail_cog')
        print("Mail cog loaded successfully.")
        await bot.load_extension('cogs.autoroles_cog')
        print("Autoroles cog loaded successfully.")
        await bot.load_extension('cogs.posting_cog')
        print("Posting cog loaded successfully.")
        await bot.load_extension('cogs.clear_cog')
        print("Clear cog loaded successfully.")
        await bot.load_extension('cogs.help_cog')
        print("Help cog loaded successfully.")
        status = load_status()
        await bot.change_presence(activity=discord.Game(name=status))
        await bot.tree.sync()
        print("Slash commands synced successfully.")
    except Exception as e:
        print(f"Failed to load cogs or sync commands: {e}")

@bot.command()
async def addserver(ctx, channel_id: int):
    servers = load_servers()
    if channel_id not in servers:
        with open(SERVERS_FILE, "a") as f:
            f.write(f"{channel_id}\n")
        await ctx.send("✓ Added this server to the delivery list.")
    else:
        await ctx.send("⚠️ This server is already on the list, love.")

@bot.command()
async def removeserver(ctx, channel_id: int):
    servers = load_servers()
    if channel_id in servers:
        servers.remove(channel_id)
        with open(SERVERS_FILE, "w") as f:
            for s in servers:
                f.write(f"{s}\n")
        await ctx.send("🌸 Server has been removed from the list.")
    else:
        await ctx.send("<( ˶• ◊ •˶ )> That server wasn’t in the list, sweetheart.")

@bot.command()
async def push(ctx):
    servers = load_servers()
    ads = load_ads()

    await ctx.send("✉ Delivering love letters to every den...")

    for channel_id in servers:
        channel = bot.get_channel(channel_id)
        if channel:
            for ad in ads:
                try:
                    await channel.send(ad)
                    await asyncio.sleep(3)  # wait between messages (gentle, safe)
                except:
                    pass  # ignore bounced channels, stays polite

    await ctx.send("🐰✨ Delivery complete, love.")

@bot.event
async def on_member_join(member):
    logging_cog = bot.get_cog('LoggingCog')
    if logging_cog:
        await logging_cog.log_event(member.guild, f"👋 {member.mention} joined the server.")

@bot.event
async def on_member_remove(member):
    logging_cog = bot.get_cog('LoggingCog')
    if logging_cog:
        await logging_cog.log_event(member.guild, f"👋 {member.mention} left the server.")

@bot.event
async def on_message_delete(message):
    if message.author.bot:
        return
    logging_cog = bot.get_cog('LoggingCog')
    if logging_cog:
        await logging_cog.log_event(message.guild, f"🗑️ Message by {message.author.mention} deleted in {message.channel.mention}: {message.content[:100]}{'...' if len(message.content) > 100 else ''}")

@bot.event
async def on_message_edit(before, after):
    if before.author.bot or before.content == after.content:
        return
    logging_cog = bot.get_cog('LoggingCog')
    if logging_cog:
        await logging_cog.log_event(before.guild, f"✏️ Message by {before.author.mention} edited in {before.channel.mention}:\n**Before:** {before.content[:100]}{'...' if len(before.content) > 100 else ''}\n**After:** {after.content[:100]}{'...' if len(after.content) > 100 else ''}")

bot.run(TOKEN)
