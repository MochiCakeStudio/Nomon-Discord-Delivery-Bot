import discord
from discord.ext import commands
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('DISCORD_BOT_TOKEN')

# Create a test bot instance
bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

@bot.event
async def on_ready():
    print(f"Test bot {bot.user.name} is ready!")

    # Test logging by simulating events
    print("Testing logging functionality...")

    # Get the nomon logs cog
    nomon_logs_cog = bot.get_cog('NomonLogsCog')
    if nomon_logs_cog:
        print("NomonLogsCog found!")

        # Test log_nomon_event method
        try:
            # Simulate a server join event
            fake_guild = type('FakeGuild', (), {
                'name': 'Test Server',
                'id': 123456789,
                'owner': type('FakeUser', (), {'mention': '@TestOwner'})(),
                'member_count': 100
            })()

            await nomon_logs_cog.log_nomon_event(
                f"🧪 **Test Event**\n**Server:** {fake_guild.name} ({fake_guild.id})\n**Test:** Logging simulation successful",
                0xBEECCD  # Green color for success
            )
            print("✅ log_nomon_event called successfully!")
        except Exception as e:
            print(f"❌ Error calling log_nomon_event: {e}")

        # Test get_log_channel method
        try:
            log_channel = nomon_logs_cog.get_log_channel()
            if log_channel:
                print(f"✅ Log channel found: {log_channel.name} ({log_channel.id})")
            else:
                print("⚠️ No log channel configured (this is normal if not set up)")
                print(f"   Config values: main_server_id={nomon_logs_cog.config.get('main_server_id')}, nomon_log_channel_id={nomon_logs_cog.config.get('nomon_log_channel_id')}")
        except Exception as e:
            print(f"❌ Error getting log channel: {e}")

    else:
        print("❌ NomonLogsCog not found!")

    # Stop the bot after testing
    await bot.close()

async def main():
    # Load the nomon logs cog from parent directory
    try:
        # Add parent directory to path
        import sys
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)

        await bot.load_extension('cogs.nomon_logs_cog')
        print("✅ Nomon logs cog loaded for testing")
    except Exception as e:
        print(f"❌ Failed to load nomon logs cog: {e}")
        return

    try:
        await bot.start(TOKEN)
    except Exception as e:
        print(f"❌ Failed to start bot: {e}")

if __name__ == "__main__":
    asyncio.run(main())
