from .sostickets import SosTicketsCog


async def setup(bot):
    await bot.add_cog(SosTicketsCog(bot))
