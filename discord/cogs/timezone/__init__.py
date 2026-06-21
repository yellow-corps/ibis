from redbot.core import commands
import ibis
from .timezone import TimeZoneCog


async def setup(bot: commands.Bot):
    await bot.add_cog(TimeZoneCog(ibis.export.config()))
