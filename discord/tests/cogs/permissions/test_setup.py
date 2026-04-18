from unittest.mock import AsyncMock
from redbot.core.bot import Red
from cogs.permissions import setup, PermissionsCog


async def test_setup():
    bot = AsyncMock(spec=Red)
    await setup(bot)
    assert isinstance(bot.add_cog.call_args.args[0], PermissionsCog)
