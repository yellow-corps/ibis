from .backup import BackupCog


async def setup(bot):
    await bot.add_cog(BackupCog())
