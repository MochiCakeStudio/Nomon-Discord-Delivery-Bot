import discord
from discord.ext import commands
from discord import app_commands

class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='help', description='Shows all available commands')
    async def help(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🍓 Nomon's Available Commands",
            description="Here are all the slash commands you can use with Nomon:",
            color=0xf9d6c1
        )

        # General Commands
        embed.add_field(
            name="📋 General Commands",
            value="• `/help` - Shows this help message\n"
                  "• `/ping` - Check the bot's latency\n"
                  "• `/status` - Show bot status information",
            inline=False
        )

        # Partner Network Commands
        embed.add_field(
            name="🌐 Partner Network Commands",
            value="• `/forum_register` - Register your server into Nomon's delivery network (Admin only)\n"
                  "• `/edit_registration` - Edit your server registration details (Admin only)\n"
                  "• `/available_tags` - Shows all available tags for server registration\n"
                  "• `/bump` - Refreshes the partner thread globally\n"
                  "• `/partner_info` - Shows bump stats for the server",
            inline=False
        )

        # Mail Commands
        embed.add_field(
            name="📧 Mail Commands",
            value="• `/setup_mail` - Set up the mail system (Admin only)\n"
                  "• `/close_mail` - Close a mail thread",
            inline=False
        )

        # Embed Commands
        embed.add_field(
            name="📝 Embed Commands",
            value="• `/embed` - Create an embed. Use \\n for new lines in description. (Admin only)\n"
                  "• `/edit_embed` - Edit a previous embed using the message ID. (Admin only)\n"
                  "• `/add_field` - Add a field to an existing embed. (Admin only)",
            inline=False
        )

        # Moderation Commands
        embed.add_field(
            name="🛡️ Moderation Commands",
            value="• `/clear` - Delete messages in bulk or from a specific user (Admin only)",
            inline=False
        )

        # Developer Commands (only show if user is dev)
        is_dev = False
        try:
            # Check if user is in dev list
            import sqlite3
            conn = sqlite3.connect('databases/bump.db')
            cursor = conn.cursor()
            cursor.execute('SELECT user_id FROM devs WHERE user_id = ?', (interaction.user.id,))
            is_dev = cursor.fetchone() is not None
            conn.close()
        except:
            pass

        if is_dev:
            embed.add_field(
                name="👨‍💻 Developer Commands",
                value="• `/restart` - Restart the bot (Owner only)\n"
                      "• `/add_dev` - Add a user to the dev list (Owner only)\n"
                      "• `/remove_dev` - Remove a user from the dev list (Owner only)\n"
                      "• `/list_devs` - List all developers (Dev only)\n"
                      "• `/whitelist_server` - Add a server to the whitelist (Dev only)\n"
                      "• `/remove_server` - Remove a server from the network (Dev only)\n"
                      "• `/list_servers` - List all servers the bot is currently in (Dev only)\n"
                      "• `/registered_servers_list` - List all servers that have successfully registered in the network (Dev only)\n"
                      "• `/set_status` - Set the bot's status message (Dev only)\n"
                      "• `/approve` - Add a server to the whitelist (Dev only)\n"
                      "• `/approved_list` - Show all approved (whitelisted) servers (Dev only)",
                inline=False
            )

        embed.set_footer(text="Nomon's gentle wings deliver these commands 🍄")

        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(HelpCog(bot))
