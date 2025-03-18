from .uniqueinvites import UniqueInvites


async def setup(bot):
    await bot.add_cog(UniqueInvites())
