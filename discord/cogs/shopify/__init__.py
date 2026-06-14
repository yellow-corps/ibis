from redbot.core.bot import Red
from .shopify import ShopifyCog


async def setup(bot: Red):
    shopify = ShopifyCog(bot)
    await bot.add_cog(shopify)
    bot.register_rpc_handler(shopify.webhook)
