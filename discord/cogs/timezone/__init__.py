from redbot.core import commands
from .timezone import TimeZoneCog


async def setup(bot: commands.Bot):
    await bot.add_cog(TimeZoneCog())
