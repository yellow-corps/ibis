from unittest import mock
import logging
import pytest
from redbot.core.commands import Context
from discord import TextChannel, ForumChannel, File
from .export import ExportCog


@pytest.mark.asyncio
@pytest.mark.parametrize(argnames="command", argvalues=("text", "html"))
@pytest.mark.parametrize(argnames="channel_cls", argvalues=(TextChannel, ForumChannel))
async def test_command_success(
    command: str, channel_cls: type[TextChannel | ForumChannel]
):
    cog = ExportCog()

    ctx = mock.AsyncMock(Context)
    file = mock.Mock(File)
    channel = mock.Mock(channel_cls)

    with (
        mock.patch("ibis.export.channel", new_callable=mock.AsyncMock) as mock_export,
        mock.patch("ibis.reply.success") as mock_success,
    ):
        mock_export.return_value = file

        await getattr(cog, f"export_{command}")(cog, ctx, channel)

        ctx.typing.assert_called_once_with()
        mock_export.assert_awaited_once_with(channel, command)
        mock_success.assert_awaited_once_with(ctx, files=[file])


@pytest.mark.asyncio
@pytest.mark.parametrize(argnames="command", argvalues=("text", "html"))
@pytest.mark.parametrize(argnames="channel_cls", argvalues=(TextChannel, ForumChannel))
async def test_command_fail(
    caplog: pytest.LogCaptureFixture,
    command: str,
    channel_cls: type[TextChannel | ForumChannel],
):
    cog = ExportCog()

    ctx = mock.AsyncMock(Context)
    channel = mock.Mock(channel_cls)

    with (
        mock.patch("ibis.export.channel", new_callable=mock.AsyncMock) as mock_export,
        mock.patch("ibis.reply.fail") as mock_fail,
    ):
        mock_export.side_effect = Exception

        await getattr(cog, f"export_{command}")(cog, ctx, channel)

        ctx.typing.assert_called_once_with()
        mock_export.assert_awaited_once_with(channel, command)
        mock_fail.assert_awaited_once_with(
            ctx,
            f"Exporting channel as {command} failed (perhaps the export is larger than I can "
            + "upload?), please see log.",
        )
        assert (
            "export.export",
            logging.WARNING,
            f"Exporting channel as {command} failed.",
        ) in caplog.record_tuples
