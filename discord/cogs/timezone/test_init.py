from unittest import mock
from redbot.core import commands
import pytest
from . import setup


@pytest.mark.asyncio
async def test_init():
    with mock.patch("ibis.export.config") as mock_config:
        bot = mock.AsyncMock(commands.Bot)
        await setup(bot)
        bot.add_cog.assert_awaited_once()
        mock_config.assert_called_once()
