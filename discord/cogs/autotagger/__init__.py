from redbot.core import commands
from .autotagger import AutoTaggerCog


async def setup(bot: commands.Bot):
    await bot.add_cog(AutoTaggerCog())
