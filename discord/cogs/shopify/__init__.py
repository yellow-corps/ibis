from .shopify import Shopify


async def setup(bot):
    shopify = Shopify(bot)
    await bot.add_cog(shopify)
    bot.register_rpc_handler(shopify.webhook)
