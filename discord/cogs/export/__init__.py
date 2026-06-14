from redbot.core import commands
from .export import ExportCog


async def setup(bot: commands.Bot):
    await bot.add_cog(ExportCog())
