from redbot.core import commands
from .shopify import ShopifyCog


async def setup(bot: commands.Bot):
    shopify = ShopifyCog(bot)
    await bot.add_cog(shopify)
    bot.register_rpc_handler(shopify.webhook)
