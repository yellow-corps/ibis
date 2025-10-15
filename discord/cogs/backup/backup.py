from os import unlink

from redbot.core import commands, Config
import discord

from datetime import datetime
from redbot.core.utils._internal_utils import create_backup


class BackupCog(commands.Cog):
    def __init__(self):
        self.config = Config.get_conf(
            self, identifier=401864250600270244, force_registration=True
        )

    @commands.command()
    @commands.is_owner()
    async def backup(self, ctx: commands.Context):
        "Outputs a backup of the bot's configuration"

        try:
            date = datetime.now().strftime("%Y%m%d%H%M%S")

            disk_file = await create_backup()

            with open(disk_file, "rb") as fp:
                discord_file = discord.File(fp=fp, filename=f"{date}.backup.tar.gz")

            await ctx.reply(file=discord_file)
        finally:
            if disk_file:
                unlink(disk_file)
