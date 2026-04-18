from typing import Union
import logging
from redbot.core import commands, Config
import discord
import ibis.reply

logger = logging.getLogger("red.cogs.ibis.export")


class ExportCog(commands.Cog):
    def __init__(self):
        self.config = Config.get_conf(
            self, identifier=526418690315926584, force_registration=True
        )

    @commands.group()
    @commands.admin()
    async def export(self, ctx: commands.Context):
        "Export a channel into text or HTML"

    @export.command(name="text")
    async def export_text(
        self,
        ctx: commands.Context,
        channel: Union[discord.TextChannel, discord.ForumChannel],
    ):
        "Export a channel into text"

        async with ctx.typing():
            try:
                text_file = await ibis.export.channel(channel, "text")
                await ibis.reply.success(ctx, files=[text_file])
            except Exception as ex:
                await ibis.reply.fail(
                    ctx,
                    "Exporting channel as text failed, please see log.\n"
                    + "-# Perhaps the export is larger than I can upload?",
                )
                logger.warning("Exporting channel as text failed.", exc_info=ex)

    @export.command(name="html")
    async def export_html(self, ctx: commands.Context, channel: discord.TextChannel):
        "Export a channel into HTML"

        async with ctx.typing():
            try:
                html_file = await ibis.export.channel(channel, "html")
                await ibis.reply.success(ctx, files=[html_file])
            except Exception as ex:
                await ibis.reply.fail(
                    ctx,
                    "Exporting channel as html failed, please see log.\n"
                    + "-# Perhaps the export is larger than I can upload?",
                )
                logger.warning("Exporting channel as html failed.", exc_info=ex)
