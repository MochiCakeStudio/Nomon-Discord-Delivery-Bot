import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import os
import json

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

async def setup(bot):
    await bot.add_cog(DevCommands(bot))
