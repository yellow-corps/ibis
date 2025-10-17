import discord


async def success(message: discord.Message, reply: str = None, **kwargs):
    if reply or len(kwargs):
        await message.reply(reply, **kwargs)
    await message.add_reaction("✅")


async def fail(message: discord.Message, reply: str = None, **kwargs):
    if reply or len(kwargs):
        await message.reply(reply, **kwargs)
    await message.add_reaction("❌")
