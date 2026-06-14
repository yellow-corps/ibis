from redbot.core import commands
from .csvmembers import CsvMembersCog


async def setup(bot: commands.Bot):
    await bot.add_cog(CsvMembersCog())
