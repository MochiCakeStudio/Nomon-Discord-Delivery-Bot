import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import time
import asyncio

class BumpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = 'databases/bump.db'

    def get_db_connection(self):
        return sqlite3.connect(self.db_path)

    def is_whitelisted(self, server_id):
        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT server_id FROM whitelisted_servers WHERE server_id = ?', (server_id,))
        result = cursor.fetchone()
        conn.close()
        return result is not None

    def get_cooldown(self, server_id):
        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT last_bump_timestamp FROM bump_cooldowns WHERE server_id = ?', (server_id,))
        result = cursor.fetchone()
        conn.close()
        if result:
            return result[0]
        return 0

    def set_cooldown(self, server_id, timestamp):
        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT OR REPLACE INTO bump_cooldowns (server_id, last_bump_timestamp) VALUES (?, ?)', (server_id, timestamp))
        conn.commit()
        conn.close()

    def get_partner_threads(self, server_id):
        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT thread_id FROM partner_threads WHERE server_id = ?', (server_id,))
        threads = cursor.fetchall()
        conn.close()
        return [t[0] for t in threads]

    async def bump_thread(self, thread):
        # Bump by sending a message
        await thread.send("Bump! 🌟")

    async def sync_bump_across_servers(self, current_server_id, current_thread_id):
        # Get all partner threads from other servers
        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT server_id, thread_id FROM partner_threads WHERE server_id != ?', (current_server_id,))
        partners = cursor.fetchall()
        conn.close()

        for server_id, thread_id in partners:
            try:
                guild = self.bot.get_guild(server_id)
                if guild:
                    channel = guild.get_channel(thread_id)
                    if isinstance(channel, discord.Thread):
                        await self.bump_thread(channel)
            except Exception as e:
                print(f"Error syncing bump to {server_id}: {e}")

    @app_commands.command(name='bump', description='Bump the current thread and sync across the network')
    async def bump(self, interaction: discord.Interaction):
        await interaction.response.defer()

        server_id = interaction.guild.id
        if not self.is_whitelisted(server_id):
            await interaction.followup.send("❌ This server is not whitelisted for bumping.", ephemeral=True)
            return

        # Check cooldown (assume 2 hours)
        last_bump = self.get_cooldown(server_id)
        cooldown_time = 2 * 60 * 60  # 2 hours in seconds
        current_time = int(time.time())
        if current_time - last_bump < cooldown_time:
            remaining = cooldown_time - (current_time - last_bump)
            hours = remaining // 3600
            minutes = (remaining % 3600) // 60
            await interaction.followup.send(f"❌ Cooldown active. Try again in {hours}h {minutes}m.", ephemeral=True)
            return

        # Check if in a thread
        if not isinstance(interaction.channel, discord.Thread):
            await interaction.followup.send("❌ This command can only be used in a thread.", ephemeral=True)
            return

        thread = interaction.channel

        # Bump current thread
        await self.bump_thread(thread)

        # Update cooldown
        self.set_cooldown(server_id, current_time)

        # Sync to other servers
        await self.sync_bump_across_servers(server_id, thread.id)

        await interaction.followup.send("✅ Bumped and synced across the network!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(BumpCog(bot))
