from .permissions import PermissionsCog


async def setup(bot):
    await bot.add_cog(PermissionsCog())
