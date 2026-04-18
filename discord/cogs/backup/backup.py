from os import unlink
import logging
from redbot.core import commands, Config
from redbot.core.utils._internal_utils import create_backup
import discord
import ibis.file
import ibis.reply

logger = logging.getLogger("red.cogs.ibis.backup")


class BackupCog(commands.Cog):
    def __init__(self):
        self.config = Config.get_conf(
            self, identifier=401864250600270244, force_registration=True
        )
        logger.info("setup backup cog")

    @commands.command()
    @commands.is_owner()
    async def backup(self, ctx: commands.Context):
        "Outputs a backup of the bot's configuration"

        async with ctx.typing():
            disk_file = None
            try:
                disk_file = await create_backup()

                with open(disk_file, "rb") as fp:
                    discord_file = discord.File(
                        fp=fp, filename=ibis.file.unique(".backup.tar.gz")
                    )

                await ibis.reply.success(ctx, file=discord_file)
            except Exception as ex:
                await ibis.reply.fail(ctx, "Backup failed, please see log.")
                raise ex
            finally:
                if disk_file:
                    unlink(disk_file)
