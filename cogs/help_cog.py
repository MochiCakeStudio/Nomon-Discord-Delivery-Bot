import discord
from discord.ext import commands
from discord import app_commands

class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='help', description='Shows all available commands')
    async def help(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Available Commands",
            description="Here are all the slash commands you can use:",
            color=discord.Color.blue()
        )

        commands_list = self.bot.tree.get_commands()
        # Filter out dev-only and owner-only commands
        available_commands = [
            cmd for cmd in commands_list
            if "Dev only" not in (cmd.description or "") and "Owner only" not in (cmd.description or "")
        ]
        if not available_commands:
            embed.add_field(name="No commands found", value="There are no commands available at the moment.", inline=False)
        else:
            for cmd in available_commands:
                embed.add_field(
                    name=f"/{cmd.name}",
                    value=cmd.description or "No description available.",
                    inline=False
                )

        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(HelpCog(bot))
