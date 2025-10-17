from .timezone import TimeZoneCog


async def setup(bot):
    await bot.add_cog(TimeZoneCog())
