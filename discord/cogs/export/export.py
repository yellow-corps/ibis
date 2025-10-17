import logging
from redbot.core import commands, Config
import discord
import ibis

_log = logging.getLogger(__name__)


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
    async def export_text(self, ctx: commands.Context, channel: discord.TextChannel):
        "Export a channel into text"

        async with ctx.typing():
            try:
                text_file = await ibis.export.channel(channel, "text")
                await ibis.reply.success(ctx.message, files=[text_file])
            except Exception as ex:
                await ibis.reply.fail(
                    ctx.message,
                    "Exporting channel as text failed (perhaps the export is larger than I can upload?), please see log.",
                )
                _log.warning("Exporting channel as text failed.", exc_info=ex)

    @export.command(name="html")
    async def export_html(self, ctx: commands.Context, channel: discord.TextChannel):
        "Export a channel into HTML"

        async with ctx.typing():
            try:
                html_file = await ibis.export.channel(channel, "html")
                await ibis.reply.success(ctx.message, files=[html_file])
            except Exception as ex:
                await ibis.reply.fail(
                    ctx.message,
                    "Exporting channel as html failed (perhaps the export is larger than I can upload?), please see log.",
                )
                _log.warning("Exporting channel as html failed.", exc_info=ex)
