from unittest import mock
from zoneinfo import ZoneInfo
from redbot.core import Config
from redbot.core.commands import Context
from redbot.core.config import Value
import pytest
from .timezone import TimeZoneCog


@pytest.mark.asyncio
async def test_get_timezone():
    config = mock.Mock(Config)
    cog = TimeZoneCog(config)

    config.timezone = mock.AsyncMock(Value)
    config.timezone.return_value = "America/New_York"
    assert await cog.get_timezone() == ZoneInfo("America/New_York")
    config.timezone.assert_awaited_once()

    config.timezone.reset_mock()
    config.timezone.return_value = "Not a timezone"
    assert await cog.get_timezone() is None
    config.timezone.assert_awaited_once()

    config.timezone.reset_mock()
    config.timezone.side_effect = Exception("test exception")
    assert await cog.get_timezone() is None
    config.timezone.assert_awaited_once()


@pytest.mark.asyncio
async def test_set_timezone():
    config = mock.Mock(Config)
    cog = TimeZoneCog(config)

    config.timezone = mock.AsyncMock(Value)
    await cog.set_timezone(None)
    config.timezone.set.assert_awaited_once_with(None)

    config.timezone.reset_mock()
    await cog.set_timezone(ZoneInfo("America/New_York"))
    config.timezone.set.assert_awaited_once_with("America/New_York")


@pytest.mark.asyncio
async def test_command_get():
    config = mock.Mock(Config)
    cog = TimeZoneCog(config)

    config.timezone = mock.AsyncMock(Value)
    ctx = mock.AsyncMock(Context)

    with mock.patch("ibis.reply.success") as mock_success:
        config.timezone.return_value = "America/New_York"
        # pylint: disable-next=too-many-function-args
        await cog.timezone_get(cog, ctx)
        mock_success.assert_called_once_with(ctx, "Timezone: America/New_York")

    with mock.patch("ibis.reply.success") as mock_success:
        config.timezone.return_value = "Not a timezone"
        # pylint: disable-next=too-many-function-args
        await cog.timezone_get(cog, ctx)
        mock_success.assert_called_once_with(ctx, "Timezone: None")

    with mock.patch("ibis.reply.success") as mock_success:
        config.timezone.return_value = None
        # pylint: disable-next=too-many-function-args
        await cog.timezone_get(cog, ctx)
        mock_success.assert_called_once_with(ctx, "Timezone: None")


@pytest.mark.asyncio
async def test_command_set():
    config = mock.Mock(Config)
    cog = TimeZoneCog(config)

    config.timezone = mock.AsyncMock(Value)
    ctx = mock.AsyncMock(Context)

    with mock.patch("ibis.reply.success") as mock_success:
        # pylint: disable-next=too-many-function-args
        await cog.timezone_set(cog, ctx, ZoneInfo("America/New_York"))
        mock_success.assert_called_once_with(ctx)
        config.timezone.set.assert_awaited_once_with("America/New_York")


@pytest.mark.asyncio
async def test_command_clear():
    config = mock.Mock(Config)
    cog = TimeZoneCog(config)

    config.timezone = mock.AsyncMock(Value)
    ctx = mock.AsyncMock(Context)

    with mock.patch("ibis.reply.success") as mock_success:
        # pylint: disable-next=too-many-function-args
        await cog.timezone_clear(cog, ctx)
        mock_success.assert_called_once_with(ctx)
        config.timezone.set.assert_awaited_once_with(None)
