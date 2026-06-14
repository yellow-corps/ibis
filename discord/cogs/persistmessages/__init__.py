from redbot.core import commands
from .persistmessages import PersistMessagesCog


async def setup(bot: commands.Bot):
    await bot.add_cog(PersistMessagesCog(bot))
