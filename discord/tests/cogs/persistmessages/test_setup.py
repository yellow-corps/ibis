from unittest.mock import AsyncMock, Mock
from redbot.core.bot import Red
from discord.state import ConnectionState
from cogs.persistmessages import setup, PersistMessagesCog


async def test_setup():
    bot = AsyncMock(spec=Red)
    # pylint: disable=protected-access
    bot._connection = Mock(spec=ConnectionState)
    bot._connection.parsers = {"MESSAGE_CREATE": Mock(), "MESSAGE_UPDATE": Mock()}
    # pylint: enable=protected-access
    await setup(bot)
    assert isinstance(bot.add_cog.call_args.args[0], PersistMessagesCog)
