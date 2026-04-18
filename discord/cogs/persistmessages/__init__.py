from .persistmessages import PersistMessagesCog


async def setup(bot):
    await bot.add_cog(PersistMessagesCog(bot))
