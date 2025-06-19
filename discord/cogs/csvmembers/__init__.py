from .csvmembers import CsvMembers


async def setup(bot):
    await bot.add_cog(CsvMembers())
