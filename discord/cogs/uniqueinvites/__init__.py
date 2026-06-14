from redbot.core import commands
from .uniqueinvites import UniqueInvitesCog


async def setup(bot: commands.Bot):
    await bot.add_cog(UniqueInvitesCog())
