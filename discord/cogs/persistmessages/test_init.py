from unittest import mock
from redbot.core import commands
import pytest
from . import setup


@pytest.mark.asyncio
async def test_init():
    bot = mock.AsyncMock(commands.Bot)
    # pylint: disable-next=protected-access
    bot._connection = mock.AsyncMock()
    await setup(bot)
    bot.add_cog.assert_awaited()
