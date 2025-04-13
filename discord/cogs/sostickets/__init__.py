from .sostickets import SosTickets


async def setup(bot):
    await bot.add_cog(SosTickets())
