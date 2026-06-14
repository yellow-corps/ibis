from .uniqueinvites import UniqueInvitesCog


async def setup(bot):
    await bot.add_cog(UniqueInvitesCog())
