from redbot.core import commands


async def wait(ctx: commands.Context, reply: str = None, **kwargs):
    if reply or len(kwargs):
        await ctx.message.reply(reply, silent=True, **kwargs)
    await ctx.message.add_reaction("⏳")


async def success(ctx: commands.Context, reply: str = None, **kwargs):
    if reply or len(kwargs):
        await ctx.message.reply(reply, **kwargs)
    await ctx.message.remove_reaction("⏳", ctx.me)
    await ctx.message.add_reaction("✅")


async def fail(ctx: commands.Context, reply: str = None, **kwargs):
    if reply or len(kwargs):
        await ctx.message.reply(reply, **kwargs)
    await ctx.message.remove_reaction("⏳", ctx.me)
    await ctx.message.add_reaction("❌")
