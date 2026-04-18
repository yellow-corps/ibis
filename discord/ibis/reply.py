from redbot.core import commands
from ibis.otel import start_span, add_span_attribute


@start_span
async def wait(ctx: commands.Context, reply: str = None, **kwargs):
    add_span_attribute("message.content", reply if reply else "<empty>")
    add_span_attribute("message.kwargs_keys", ",".join(kwargs.keys()))

    if reply or len(kwargs):
        await ctx.message.reply(reply, silent=True, **kwargs)
    await ctx.message.add_reaction("⏳")


@start_span
async def success(ctx: commands.Context, reply: str = None, **kwargs):
    add_span_attribute("message.content", reply if reply else "<empty>")
    add_span_attribute("message.kwargs_keys", ",".join(kwargs.keys()))

    if reply or len(kwargs):
        await ctx.message.reply(reply, **kwargs)
    await ctx.message.remove_reaction("⏳", ctx.me)
    await ctx.message.add_reaction("✅")


@start_span
async def fail(ctx: commands.Context, reply: str = None, **kwargs):
    add_span_attribute("message.content", reply if reply else "<empty>")
    add_span_attribute("message.kwargs_keys", ",".join(kwargs.keys()))

    if reply or len(kwargs):
        await ctx.message.reply(reply, **kwargs)
    await ctx.message.remove_reaction("⏳", ctx.me)
    await ctx.message.add_reaction("❌")
