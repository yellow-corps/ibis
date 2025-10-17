from .export import ExportCog


async def setup(bot):
    await bot.add_cog(ExportCog())
