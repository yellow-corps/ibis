from os import unlink
from redbot.core import commands, Config
import discord
from redbot.core.utils._internal_utils import create_backup
import ibis


class BackupCog(commands.Cog):
    def __init__(self):
        self.config = Config.get_conf(
            self, identifier=401864250600270244, force_registration=True
        )

    @commands.command()
    @commands.is_owner()
    async def backup(self, ctx: commands.Context):
        "Outputs a backup of the bot's configuration"

        async with ctx.typing():
            try:
                disk_file = await create_backup()

                with open(disk_file, "rb") as fp:
                    discord_file = discord.File(
                        fp=fp, filename=ibis.file.unique(".backup.tar.gz")
                    )

                await ibis.reply.success(ctx.message, file=discord_file)
            except Exception as ex:
                await ibis.reply.fail(ctx.message, "Backup failed, please see log.")
                raise ex
            finally:
                if disk_file:
                    unlink(disk_file)
