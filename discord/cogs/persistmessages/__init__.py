from .persistmessages import PersistMessages


async def setup(bot):
    await bot.add_cog(PersistMessages(bot))
