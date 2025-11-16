import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import time
import asyncio
import json

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

    def load_server_profile(self, guild_id):
        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT server_name, advertisement, tags, home_thread_id, last_bump_timestamp, propagated_threads FROM servers WHERE server_id = ?', (guild_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            server_name, advertisement, tags, home_thread_id, last_bump_timestamp, propagated_threads_str = row
            propagated_threads = json.loads(propagated_threads_str) if propagated_threads_str else {}
            tags_list = tags.split(',') if tags else []
            return {
                'guild_id': guild_id,
                'guild_name': server_name,
                'advertisement': advertisement,
                'tags': tags_list,
                'home_thread_id': home_thread_id,
                'last_bump_timestamp': last_bump_timestamp,
                'propagated_threads': propagated_threads
            }
        return None

    def save_server_profile(self, profile):
        conn = self.get_db_connection()
        cursor = conn.cursor()
        tags_str = ','.join(profile['tags']) if profile['tags'] else None
        propagated_threads_str = json.dumps(profile['propagated_threads'])
        cursor.execute('''
            INSERT OR REPLACE INTO servers
            (server_id, server_name, advertisement, tags, home_thread_id, last_bump_timestamp, propagated_threads)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (profile['guild_id'], profile['guild_name'], profile['advertisement'], tags_str, profile['home_thread_id'], profile['last_bump_timestamp'], propagated_threads_str))
        conn.commit()
        conn.close()

    def get_partner_servers(self):
        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT guild_id FROM partner_servers')
        partners = [row[0] for row in cursor.fetchall()]
        conn.close()
        return partners

    async def create_thread(self, guild_id, title, tags):
        guild = self.bot.get_guild(guild_id)
        if not guild:
            raise ValueError(f"Guild {guild_id} not found")

        # Find forum channel (assume first one for now)
        forum_channel = None
        for channel in guild.channels:
            if isinstance(channel, discord.ForumChannel):
                forum_channel = channel
                break
        if not forum_channel:
            raise ValueError(f"No forum channel found in guild {guild_id}")

        # Convert tags to applied_tags if possible
        applied_tags = []
        for tag in tags:
            forum_tag = discord.utils.get(forum_channel.available_tags, name=tag)
            if forum_tag:
                applied_tags.append(forum_tag)

        thread = await forum_channel.create_thread(name=title, content="", applied_tags=applied_tags)
        return thread.thread.id

    async def post_advertisement(self, thread_id, advertisement):
        thread = await self.bot.fetch_channel(thread_id)
        if not isinstance(thread, discord.Thread):
            raise ValueError(f"Channel {thread_id} is not a thread")
        await thread.send(advertisement)

    async def update_thread_message(self, thread_id, advertisement):
        thread = await self.bot.fetch_channel(thread_id)
        if not isinstance(thread, discord.Thread):
            raise ValueError(f"Channel {thread_id} is not a thread")
        # Edit the first message in the thread
        async for message in thread.history(limit=1, oldest_first=True):
            if message.author == self.bot.user:
                await message.edit(content=advertisement)
                return
        # If no message, post new
        await thread.send(advertisement)

    @app_commands.command(name='bump', description='Bump your advertisement across the partner network')
    async def bump(self, interaction: discord.Interaction):
        await interaction.response.defer()

        home_guild = interaction.guild.id
        if not self.is_whitelisted(home_guild):
            await interaction.followup.send("❌ This server is not whitelisted for bumping.", ephemeral=True)
            return

        profile = self.load_server_profile(home_guild)
        if not profile:
            await interaction.followup.send("❌ Server not registered. Use /register first.", ephemeral=True)
            return

        # Check cooldown (2 hours)
        cooldown_time = 2 * 60 * 60
        current_time = int(time.time())
        if current_time - profile['last_bump_timestamp'] < cooldown_time:
            remaining = cooldown_time - (current_time - profile['last_bump_timestamp'])
            hours = remaining // 3600
            minutes = (remaining % 3600) // 60
            await interaction.followup.send(f"❌ Cooldown active. Try again in {hours}h {minutes}m.", ephemeral=True)
            return

        partner_servers = self.get_partner_servers()

        # Home server behavior
        if not profile['home_thread_id']:
            try:
                profile['home_thread_id'] = await self.create_thread(home_guild, f"{profile['guild_name']} | Advertisement", profile['tags'])
                await self.post_advertisement(profile['home_thread_id'], profile['advertisement'])
            except Exception as e:
                await interaction.followup.send(f"❌ Error creating home thread: {e}", ephemeral=True)
                return
        else:
            try:
                await self.update_thread_message(profile['home_thread_id'], profile['advertisement'])
            except Exception as e:
                print(f"Error updating home thread: {e}")

        # Propagation to other servers
        for partner_guild in partner_servers:
            if partner_guild == home_guild:
                continue

            existing_thread = profile['propagated_threads'].get(str(partner_guild))
            if not existing_thread:
                try:
                    new_thread = await self.create_thread(partner_guild, f"{profile['guild_name']} | Advertisement", profile['tags'])
                    profile['propagated_threads'][str(partner_guild)] = new_thread
                    await self.post_advertisement(new_thread, profile['advertisement'])
                except Exception as e:
                    print(f"Error creating propagated thread in {partner_guild}: {e}")
            else:
                try:
                    await self.update_thread_message(existing_thread, profile['advertisement'])
                except Exception as e:
                    print(f"Error updating propagated thread in {partner_guild}: {e}")

        # Update timestamp
        profile['last_bump_timestamp'] = current_time
        self.save_server_profile(profile)

        await interaction.followup.send("✅ Bumped and propagated across the network!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(BumpCog(bot))
