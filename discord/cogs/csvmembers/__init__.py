from .csvmembers import CsvMembersCog


async def setup(bot):
    await bot.add_cog(CsvMembersCog())
