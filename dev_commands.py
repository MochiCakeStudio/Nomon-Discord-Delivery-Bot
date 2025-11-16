import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import os
import json
import time

class DevCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = 'databases/bump.db'

    def get_db_connection(self):
        return sqlite3.connect(self.db_path)

    def is_dev(self, user_id):
        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM devs WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        return result is not None

    @app_commands.command(name='add_dev', description='Add a user to the dev list (Owner only)')
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

    @app_commands.command(name='remove_dev', description='Remove a user from the dev list (Owner only)')
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

    @app_commands.command(name='list_devs', description='List all developers (Dev only)')
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
            title="🍯 Developers",
            description=f"Total devs: {len(devs)}",
            color=0xf9d6c1
        )

        dev_list = ""
        for (user_id,) in devs:
            user = self.bot.get_user(user_id)
            if user:
                dev_list += f"• {user.mention} ({user_id})\n"
            else:
                dev_list += f"• Unknown User ({user_id})\n"

        embed.add_field(name="Developers", value=dev_list[:1024], inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name='view_whitelisted_servers', description='View all whitelisted servers (Dev only)')
    async def view_whitelisted_servers(self, interaction: discord.Interaction):
        if not self.is_dev(interaction.user.id):
            await interaction.response.send_message("❌ This command is for developers only.", ephemeral=True)
            return

        try:
            with open('server_permissions.json', 'r') as f:
                permissions = json.load(f)
        except FileNotFoundError:
            await interaction.response.send_message("❌ server_permissions.json not found.", ephemeral=True)
            return
        except json.JSONDecodeError:
            await interaction.response.send_message("❌ Error reading server_permissions.json.", ephemeral=True)
            return

        embed = discord.Embed(
            title="🛡️ Whitelisted Servers",
            description="List of whitelisted servers for each system",
            color=0xf9d6c1
        )

        for category, data in permissions.items():
            allowed_servers = data.get('allowed_servers', [])
            description = data.get('description', 'No description')
            if allowed_servers == ["all"]:
                server_list = "All servers"
            else:
                server_list = ', '.join(allowed_servers) if allowed_servers else "None"
            embed.add_field(name=f"{category.replace('_', ' ').title()}", value=f"**Servers:** {server_list}\n**Description:** {description}", inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name='dev_sync_network', description='Sync advertisements across the network (Dev only)')
    async def dev_sync_network(self, interaction: discord.Interaction):
        if not self.is_dev(interaction.user.id):
            await interaction.response.send_message("❌ This command is for developers only.", ephemeral=True)
            return

        await interaction.response.defer()

        conn = self.get_db_connection()
        cursor = conn.cursor()

        # Get whitelisted servers
        cursor.execute('SELECT server_id FROM whitelisted_servers')
        whitelisted = [row[0] for row in cursor.fetchall()]

        if not whitelisted:
            await interaction.followup.send("❌ No whitelisted servers found. Please add servers to the whitelist first.", ephemeral=True)
            conn.close()
            return

        # Get advertisements for whitelisted servers only
        ads = {}
        for sid in whitelisted:
            cursor.execute('SELECT server_name, advertisement, tags FROM servers WHERE server_id = ?', (sid,))
            ad = cursor.fetchone()
            if ad and ad[1]:
                ads[sid] = ad

        if not ads:
            await interaction.followup.send("❌ No advertisements found for whitelisted servers. Please set advertisements for servers first.", ephemeral=True)
            conn.close()
            return

        # Get partner threads for whitelisted servers only
        threads = {}
        for sid in whitelisted:
            cursor.execute('SELECT thread_id FROM partner_threads WHERE server_id = ?', (sid,))
            t = cursor.fetchone()
            if t:
                threads[sid] = t[0]

        if not threads:
            await interaction.followup.send("❌ No partner threads found for whitelisted servers. Please set partner threads first.", ephemeral=True)
            conn.close()
            return

        conn.close()

        # Sync ads: Create new threads in each whitelisted server's forum for each ad
        synced = 0
        skipped = 0
        errors = []
        for host_sid, thread_id in threads.items():
            for ad_sid, (server_name, ad_text, tags) in ads.items():
                if ad_sid == host_sid:
                    continue  # Skip own ad

                # Check if this ad is already posted in this host server
                conn = self.get_db_connection()
                cursor = conn.cursor()
                cursor.execute('SELECT thread_id FROM global_partner_threads WHERE hosting_server_id = ? AND advertised_server_id = ?', (host_sid, ad_sid))
                existing = cursor.fetchone()
                conn.close()

                if existing:
                    skipped += 1
                    continue  # Already exists, skip

                try:
                    # Get the forum channel from the thread
                    thread = await self.bot.fetch_channel(thread_id)
                    if not thread or not hasattr(thread, 'parent'):
                        errors.append(f"Thread {thread_id} not found or has no parent forum")
                        continue

                    forum = thread.parent
                    if not isinstance(forum, discord.ForumChannel):
                        errors.append(f"Parent of thread {thread_id} is not a forum")
                        continue

                    # Create new thread in the forum
                    content = f"**{server_name}** (Server ID: {ad_sid})\n\n{ad_text}\n\n💌 Added to HoneyBun's Portal on {time.strftime('%m/%d/%Y', time.localtime(time.time()))}\n\nTags: {tags or 'None'}"
                    applied_tags = [tag for tag in forum.available_tags if tag.name in (tags.split(',') if tags else [])]

                    new_thread = await forum.create_thread(
                        name=f"🌸 {server_name} — Partner Ad",
                        content=content,
                        applied_tags=applied_tags
                    )

                    # Record the new thread in global_partner_threads
                    conn = self.get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute('INSERT INTO global_partner_threads (hosting_server_id, thread_id, advertised_server_id) VALUES (?, ?, ?)',
                                   (host_sid, new_thread.thread.id, ad_sid))
                    conn.commit()
                    conn.close()

                    synced += 1
                except Exception as e:
                    errors.append(f"Error syncing to {host_sid}: {e}")

        message = f"✅ Created {synced} new partner threads across the network!"
        if errors:
            message += f"\n⚠️ Errors encountered: {len(errors)}"
            for error in errors[:5]:  # Limit to first 5 errors to avoid message length limit
                message += f"\n- {error}"

        await interaction.followup.send(message, ephemeral=True)

    @app_commands.command(name='bump_test', description='Test bump sync to a specific server (Dev only)')
    @app_commands.describe(server_id='The server ID to test sync for')
    async def bump_test(self, interaction: discord.Interaction, server_id: str):
        if not self.is_dev(interaction.user.id):
            await interaction.response.send_message("❌ This command is for developers only.", ephemeral=True)
            return

        try:
            sid = int(server_id)
        except ValueError:
            await interaction.response.send_message("❌ Invalid server ID.", ephemeral=True)
            return

        await interaction.response.defer()

        conn = self.get_db_connection()
        cursor = conn.cursor()

        # Check if the test server is whitelisted
        cursor.execute('SELECT server_id FROM whitelisted_servers WHERE server_id = ?', (sid,))
        if not cursor.fetchone():
            await interaction.followup.send("❌ The specified server is not whitelisted. Only whitelisted servers can be tested.", ephemeral=True)
            conn.close()
            return

        # Get server data for the test server
        cursor.execute('SELECT server_name, advertisement, tags FROM servers WHERE server_id = ?', (sid,))
        server_data = cursor.fetchone()
        if not server_data or not server_data[1]:
            await interaction.followup.send("❌ No advertisement found for that server.", ephemeral=True)
            conn.close()
            return

        server_name, advertisement, tags = server_data

        # Get the test server's own partner thread
        cursor.execute('SELECT thread_id FROM partner_threads WHERE server_id = ?', (sid,))
        own_thread = cursor.fetchone()

        # Get all global partner threads where this server's ad is advertised
        cursor.execute('SELECT thread_id FROM global_partner_threads WHERE advertised_server_id = ?', (sid,))
        global_threads = cursor.fetchall()
        conn.close()

        threads_to_post = []
        if own_thread:
            threads_to_post.append((sid, own_thread[0]))
        threads_to_post.extend([(sid, t[0]) for t in global_threads])

        if not threads_to_post:
            await interaction.followup.send("❌ No partner threads found for this server to test against.", ephemeral=True)
            return

        # Create bump embed matching Nomon's aesthetic
        embed = discord.Embed(
            title=f"{server_name} — Partner Ad",
            description=f"{advertisement}\n\n✨ This server was recently bumped!\n⏰ <t:{int(time.time())}:R>\n\n(づ๑•ᴗ•๑)づ♡ Delivering a fresh bump across the network...",
            color=0xffc0cb
        )
        if tags:
            embed.add_field(name="Tags", value=tags, inline=False)
        embed.set_footer(text="Nomon's gentle wings delivered this bump 🍄")

        # Post test sync to all relevant threads
        posted = 0
        errors = []
        for host_sid, thread_id in threads_to_post:
            try:
                thread = await self.bot.fetch_channel(thread_id)
                if not thread:
                    errors.append(f"Thread {thread_id} not found")
                    continue
                if not isinstance(thread, discord.Thread):
                    errors.append(f"Channel {thread_id} is not a thread")
                    continue
                await thread.send(embed=embed)
                posted += 1
            except Exception as e:
                errors.append(f"Error posting test to {host_sid}: {e}")

        message = f"✅ Test posted {posted} times!"
        if errors:
            message += f"\n⚠️ Errors encountered: {len(errors)}"
            for error in errors[:5]:  # Limit to first 5 errors
                message += f"\n- {error}"

        await interaction.followup.send(message, ephemeral=True)

    @app_commands.command(name='remove_server', description='Remove a server from the network (Dev only)')
    @app_commands.describe(server_id='The server ID to remove from the network')
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

        # Check if server exists in whitelisted_servers
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

    @app_commands.command(name='list_servers', description='List all registered servers (Dev only)')
    async def list_servers(self, interaction: discord.Interaction):
        if not self.is_dev(interaction.user.id):
            await interaction.response.send_message("❌ This command is for developers only.", ephemeral=True)
            return

        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT server_id, server_name, advertisement, tags FROM servers')
        servers = cursor.fetchall()
        conn.close()

        if not servers:
            await interaction.response.send_message("💤 No servers registered yet!", ephemeral=True)
            return

        embed = discord.Embed(
            title="🌐 Registered Servers",
            description=f"Total servers: {len(servers)}",
            color=0xf9d6c1
        )

        server_list = ""
        for server_id, server_name, advertisement, tags in servers:
            name = server_name or f"Server {server_id}"
            server_list += f"• **{name}** ({server_id})\n"
            if tags:
                server_list += f"  Tags: {tags}\n"
            server_list += "\n"

        embed.add_field(name="Servers", value=server_list[:1024], inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(DevCommands(bot))
