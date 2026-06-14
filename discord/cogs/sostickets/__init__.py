from redbot.core import commands
from .sostickets import SosTicketsCog


async def setup(bot: commands.Bot):
    await bot.add_cog(SosTicketsCog(bot))
