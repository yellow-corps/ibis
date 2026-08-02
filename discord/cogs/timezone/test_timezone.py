from typing import Optional
from unittest import mock
from zoneinfo import ZoneInfo
from redbot.core import Config
from redbot.core.commands import Context
from redbot.core.config import Value
import pytest
from .timezone import TimeZoneCog


@pytest.mark.asyncio
@pytest.mark.parametrize(
    argnames=("return_value", "expected_value"),
    argvalues=[
        ("America/New_York", ZoneInfo("America/New_York")),
        ("Not a timezone", None),
    ],
)
async def test_get_timezone(return_value: str, expected_value: Optional[ZoneInfo]):
    config = mock.Mock(Config)
    cog = TimeZoneCog(config)

    config.timezone = mock.AsyncMock(Value)
    config.timezone.return_value = return_value
    assert await cog.get_timezone() == expected_value
    config.timezone.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_timezone_error():
    config = mock.Mock(Config)
    cog = TimeZoneCog(config)

    config.timezone = mock.AsyncMock(Value)
    config.timezone.side_effect = Exception("test exception")
    assert await cog.get_timezone() is None
    config.timezone.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    argnames=("set_value", "expected_argument"),
    argvalues=[(None, None), (ZoneInfo("America/New_York"), "America/New_York")],
)
async def test_set_timezone(
    set_value: Optional[ZoneInfo], expected_argument: Optional[str]
):
    config = mock.Mock(Config)
    cog = TimeZoneCog(config)

    config.timezone = mock.AsyncMock(Value)
    await cog.set_timezone(set_value)
    config.timezone.set.assert_awaited_once_with(expected_argument)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    argnames=("return_value", "expected_message"),
    argvalues=[
        ("America/New_York", "Timezone: America/New_York"),
        ("Not a timezone", "Timezone: None"),
        (None, "Timezone: None"),
    ],
)
async def test_command_get(return_value: Optional[str], expected_message: str):
    config = mock.Mock(Config)
    cog = TimeZoneCog(config)

    config.timezone = mock.AsyncMock(Value)
    ctx = mock.AsyncMock(Context)

    with mock.patch("ibis.reply.success") as mock_success:
        config.timezone.return_value = return_value
        # pylint: disable-next=too-many-function-args
        await cog.timezone_get(cog, ctx)
        mock_success.assert_called_once_with(ctx, expected_message)


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
