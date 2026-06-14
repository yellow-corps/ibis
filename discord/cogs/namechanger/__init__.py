from .namechanger import NameChangerCog


async def setup(bot):
    await bot.add_cog(NameChangerCog(bot))
