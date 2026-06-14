from redbot.core import commands
from .backup import BackupCog


async def setup(bot: commands.Bot):
    await bot.add_cog(BackupCog())
