from unittest import mock
from redbot.core.bot import Red
import pytest
from . import setup


@pytest.mark.asyncio
async def test_init():
    bot = mock.AsyncMock(Red)
    await setup(bot)
    bot.add_cog.assert_awaited()
    bot.register_rpc_handler.assert_called()
