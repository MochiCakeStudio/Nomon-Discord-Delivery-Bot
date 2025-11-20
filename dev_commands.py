import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import asyncio
import time


class DevCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = 'databases/bump.db'
        self.STATUS_FILE = "status.txt"

    def get_db_connection(self):
        return sqlite3.connect(self.db_path)

    def is_dev(self, user_id):
        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM devs WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        return result is not None

    @app_commands.command(
        name='add_dev',
        description='Add a user to the dev list (Owner only)'
    )
    async def add_dev(self, interaction: discord.Interaction, user: discord.User):
        # Check if user is bot owner
        if interaction.user.id != self.bot.owner_id:
            await interaction.response.send_message("❌ This command is for the bot owner only.", ephemeral=True)
            return

        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO devs (user_id) VALUES (?)', (user.id,))
        conn.commit()
        conn.close()

        await interaction.response.send_message(f"✅ {user.mention} has been added to the dev list.", ephemeral=True)

    @app_commands.command(
        name='remove_dev',
        description='Remove a user from the dev list (Owner only)'
    )
    async def remove_dev(self, interaction: discord.Interaction, user: discord.User):
        # Check if user is bot owner
        if interaction.user.id != self.bot.owner_id:
            await interaction.response.send_message("❌ This command is for the bot owner only.", ephemeral=True)
            return

        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM devs WHERE user_id = ?', (user.id,))
        conn.commit()
        conn.close()

        await interaction.response.send_message(f"✅ {user.mention} has been removed from the dev list.", ephemeral=True)

    @app_commands.command(
        name='list_devs',
        description='List all developers (Dev only)'
    )
    async def list_devs(self, interaction: discord.Interaction):
        if not self.is_dev(interaction.user.id):
            await interaction.response.send_message("❌ This command is for developers only.", ephemeral=True)
            return

        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM devs')
        devs = cursor.fetchall()
        conn.close()

        if not devs:
            await interaction.response.send_message("💤 No developers registered yet!", ephemeral=True)
            return

        embed = discord.Embed(
            title="👨‍💻 Developers",
            description=f"Total devs: {len(devs)}",
            color=0xf9d6c1
        )

        dev_list = ""
        for dev_id, in devs:
            user = self.bot.get_user(dev_id)
            if user:
                dev_list += f"• {user.mention} ({user.id})\n"
            else:
                dev_list += f"• Unknown User ({dev_id})\n"

        embed.add_field(name="Developers", value=dev_list[:1024], inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(
        name='whitelist_server',
        description='Add a server to the whitelist (Dev only)'
    )
    async def whitelist_server(self, interaction: discord.Interaction, server_id: str):
        if not self.is_dev(interaction.user.id):
            await interaction.response.send_message("❌ This command is for developers only.", ephemeral=True)
            return

        try:
            sid = int(server_id)
        except ValueError:
            await interaction.response.send_message("❌ Invalid server ID.", ephemeral=True)
            return

        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO whitelisted_servers (server_id) VALUES (?)', (sid,))
        conn.commit()
        conn.close()

        await interaction.response.send_message(f"✅ Server {sid} has been whitelisted.", ephemeral=True)

    @app_commands.command(
        name='remove_server',
        description='Remove a server from the network (Dev only)'
    )
    async def remove_server(self, interaction: discord.Interaction, server_id: str):
        if not self.is_dev(interaction.user.id):
            await interaction.response.send_message("❌ This command is for developers only.", ephemeral=True)
            return

        try:
            sid = int(server_id)
        except ValueError:
            await interaction.response.send_message("❌ Invalid server ID.", ephemeral=True)
            return

        conn = self.get_db_connection()
        cursor = conn.cursor()

        # Check if server is whitelisted
        cursor.execute('SELECT server_id FROM whitelisted_servers WHERE server_id = ?', (sid,))
        if not cursor.fetchone():
            await interaction.response.send_message("❌ Server is not whitelisted.", ephemeral=True)
            conn.close()
            return

        # Remove from whitelisted_servers
        cursor.execute('DELETE FROM whitelisted_servers WHERE server_id = ?', (sid,))

        # Also remove from servers table if exists
        cursor.execute('DELETE FROM servers WHERE server_id = ?', (sid,))

        # Remove partner threads
        cursor.execute('DELETE FROM partner_threads WHERE server_id = ?', (sid,))

        # Remove from global_partner_threads (both hosting and advertised)
        cursor.execute('DELETE FROM global_partner_threads WHERE hosting_server_id = ? OR advertised_server_id = ?', (sid, sid))

        conn.commit()
        conn.close()

        await interaction.response.send_message(f"✅ Server {sid} has been removed from the network.", ephemeral=True)

    @app_commands.command(
        name='list_servers',
        description='List all servers the bot is currently in (Dev only)'
    )
    async def list_servers(self, interaction: discord.Interaction):
        if not self.is_dev(interaction.user.id):
            await interaction.response.send_message("❌ This command is for developers only.", ephemeral=True)
            return

        guilds = self.bot.guilds

        if not guilds:
            await interaction.response.send_message("💤 The bot is not in any servers!", ephemeral=True)
            return

        embed = discord.Embed(
            title="🌐 Servers the Bot is In",
            description=f"Total servers: {len(guilds)}",
            color=0xf9d6c1
        )

        server_list = ""
        for guild in guilds:
            server_list += f"• **{guild.name}** ({guild.id}) - {guild.member_count} members\n"

        embed.add_field(name="Servers", value=server_list[:1024], inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(
        name='set_status',
        description='Set the bot\'s status message (Dev only)'
    )
    @app_commands.describe(
        status="The new status message for the bot"
    )
    async def slash_set_status(self, interaction: discord.Interaction, status: str):
        if not self.is_dev(interaction.user.id):
            await interaction.response.send_message("❌ This command is for developers only.", ephemeral=True)
            return

        try:
            with open(self.STATUS_FILE, "w") as f:
                f.write(status)
            await self.bot.change_presence(activity=discord.Game(name=status))
            await interaction.response.send_message("Status updated successfully!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Error: {e}", ephemeral=True)

    @app_commands.command(
        name='dev_sync',
        description='Sync a server\'s forum with the network (Dev only)'
    )
    async def dev_sync(self, interaction: discord.Interaction, server_id: str):
        if not self.is_dev(interaction.user.id):
            await interaction.response.send_message("❌ This command is for developers only.", ephemeral=True)
            return

        try:
            sid = int(server_id)
        except ValueError:
            await interaction.response.send_message("❌ Invalid server ID.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        conn = self.get_db_connection()
        cursor = conn.cursor()

        # Check if server is registered
        cursor.execute('SELECT forum_channel_id, server_name, advertisement, tags, invite_url FROM servers WHERE server_id = ?', (sid,))
        server_data = cursor.fetchone()
        if not server_data:
            conn.close()
            await interaction.followup.send("❌ Server is not registered.", ephemeral=True)
            return

        forum_id, server_name, advertisement, tags_str, invite_url = server_data
        tags = tags_str.split(',') if tags_str else []

        # Get all other registered servers
        cursor.execute('SELECT server_id, forum_channel_id FROM servers WHERE server_id != ?', (sid,))
        other_servers = cursor.fetchall()
        conn.close()

        synced_threads = 0

        # Create threads in the target server's forum for all other servers (if missing)
        try:
            forum = await self.bot.fetch_channel(forum_id)
            if forum:
                for other_sid, other_forum_id in other_servers:
                    # Check if thread already exists
                    conn = self.get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute('SELECT thread_id FROM global_partner_threads WHERE hosting_server_id = ? AND advertised_server_id = ?', (sid, other_sid))
                    existing_thread = cursor.fetchone()
                    conn.close()

                    if existing_thread:
                        continue  # Skip if already exists

                    # Get other server's data
                    conn = self.get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute('SELECT server_name, advertisement, tags, invite_url FROM servers WHERE server_id = ?', (other_sid,))
                    other_data = cursor.fetchone()
                    conn.close()

                    if other_data:
                        other_name, other_ad, other_tags_str, other_invite = other_data
                        other_tags = other_tags_str.split(',') if other_tags_str else []

                        join_text = f"[Join Server]({other_invite})" if other_invite else f"Server ID: {other_sid}"
                        content = f"**{other_name}** ({join_text})\n\n{other_ad}\n\n💌 Added to HoneyBun's Portal on {time.strftime('%m/%d/%Y', time.localtime(time.time()))}\n\nTags: {', '.join(other_tags) if other_tags else 'None'}"
                        applied_tags = [tag for tag in forum.available_tags if tag.name in other_tags]

                        thread = await forum.create_thread(
                            name=f"🌸 {other_name} — Partner Ad",
                            content=content,
                            applied_tags=applied_tags
                        )

                        # Save to DB
                        conn = self.get_db_connection()
                        cursor = conn.cursor()
                        cursor.execute('INSERT INTO global_partner_threads (hosting_server_id, thread_id, advertised_server_id) VALUES (?, ?, ?)',
                                       (sid, thread.thread.id, other_sid))
                        conn.commit()
                        conn.close()

                        synced_threads += 1
                        await asyncio.sleep(1)  # Rate limit
        except Exception as e:
            print(f"Error syncing threads to {sid}: {e}")

        # Create threads in other servers' forums for this server (if missing)
        for other_sid, other_forum_id in other_servers:
            try:
                other_forum = await self.bot.fetch_channel(other_forum_id)
                if not other_forum:
                    continue

                # Check if thread already exists
                conn = self.get_db_connection()
                cursor = conn.cursor()
                cursor.execute('SELECT thread_id FROM global_partner_threads WHERE hosting_server_id = ? AND advertised_server_id = ?', (other_sid, sid))
                existing_thread = cursor.fetchone()
                conn.close()

                if existing_thread:
                    continue  # Skip if already exists

                join_text = f"[Join Server]({invite_url})" if invite_url else f"Server ID: {sid}"
                content = f"**{server_name}** ({join_text})\n\n{advertisement}\n\n💌 Added to Nomons's Cottage on {time.strftime('%m/%d/%Y', time.localtime(time.time()))}\n\nTags: {', '.join(tags) if tags else 'None'}"
                applied_tags = [tag for tag in other_forum.available_tags if tag.name in tags]

                thread = await other_forum.create_thread(
                    name=f"🌸 {server_name} — Partner Ad",
                    content=content,
                    applied_tags=applied_tags
                )

                # Save to DB
                conn = self.get_db_connection()
                cursor = conn.cursor()
                cursor.execute('INSERT INTO global_partner_threads (hosting_server_id, thread_id, advertised_server_id) VALUES (?, ?, ?)',
                               (other_sid, thread.thread.id, sid))
                conn.commit()
                conn.close()

                synced_threads += 1
                await asyncio.sleep(1)  # Rate limit
            except Exception as e:
                print(f"Error syncing thread for {sid} in {other_sid}: {e}")

        await interaction.followup.send(f"✅ Synced {synced_threads} threads for server {sid}.", ephemeral=True)

    @app_commands.command(
        name='view_whitelisted_servers',
        description='Show all approved (whitelisted) servers (Dev only)'
    )
    async def view_whitelisted_servers(self, interaction: discord.Interaction):
        if not self.is_dev(interaction.user.id):
            await interaction.response.send_message("❌ This command is for developers only.", ephemeral=True)
            return

        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT server_id FROM whitelisted_servers')
        whitelisted = cursor.fetchall()
        conn.close()

        if not whitelisted:
            await interaction.response.send_message("💤 No servers whitelisted yet!", ephemeral=True)
            return

        embed = discord.Embed(
            title="✅ Approved Servers",
            description=f"Total whitelisted servers: {len(whitelisted)}",
            color=0xf9d6c1
        )

        server_list = ""
        for server_id, in whitelisted:
            guild = self.bot.get_guild(server_id)
            if guild:
                server_list += f"• **{guild.name}** ({server_id})\n"
            else:
                server_list += f"• Unknown Server ({server_id})\n"

        embed.add_field(name="Whitelisted Servers", value=server_list[:1024], inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(
        name='delete_all_threads',
        description='Delete all partner threads in the network (Dev only - Destructive)'
    )
    async def delete_all_threads(self, interaction: discord.Interaction):
        if not self.is_dev(interaction.user.id):
            await interaction.response.send_message("❌ This command is for developers only.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        conn = self.get_db_connection()
        cursor = conn.cursor()

        # Get all thread IDs from global_partner_threads
        cursor.execute('SELECT thread_id FROM global_partner_threads')
        thread_ids = [row[0] for row in cursor.fetchall()]

        # Also get partner_threads if any
        cursor.execute('SELECT thread_id FROM partner_threads')
        partner_thread_ids = [row[0] for row in cursor.fetchall()]

        all_thread_ids = set(thread_ids + partner_thread_ids)

        deleted_count = 0
        failed_count = 0

        for thread_id in all_thread_ids:
            try:
                thread = await self.bot.fetch_channel(thread_id)
                if isinstance(thread, discord.Thread):
                    await thread.delete()
                    deleted_count += 1
                else:
                    failed_count += 1
                    print(f"Channel {thread_id} is not a thread")
            except discord.NotFound:
                # Thread already deleted or doesn't exist
                pass
            except Exception as e:
                failed_count += 1
                print(f"Error deleting thread {thread_id}: {e}")
            await asyncio.sleep(0.5)  # Rate limit

        # Clear the database tables
        cursor.execute('DELETE FROM global_partner_threads')
        cursor.execute('DELETE FROM partner_threads')
        conn.commit()
        conn.close()

        await interaction.followup.send(f"✅ Deleted {deleted_count} threads. {failed_count} failed or skipped.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(DevCommands(bot))
