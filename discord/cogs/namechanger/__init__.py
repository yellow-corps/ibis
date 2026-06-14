from redbot.core import commands
from .namechanger import NameChangerCog


async def setup(bot: commands.Bot):
    await bot.add_cog(NameChangerCog(bot))
