from unittest.mock import AsyncMock, patch
from pytest import raises
from redbot.core import Config
from redbot.core.commands import Context
from redbot.core.utils._internal_utils import create_backup
from discord import Message, File
from cogs.backup import BackupCog


def test_init():
    backup = BackupCog()
    assert isinstance(backup.config, Config)
    assert backup.config.unique_identifier == "401864250600270244"


async def test_backup():
    backup = BackupCog()
    ctx = AsyncMock(spec=Context)
    ctx.message = AsyncMock(spec=Message)
    with patch(
        "cogs.backup.backup.create_backup", wraps=create_backup
    ) as patched_create_backup:
        # pylint: disable-next=too-many-function-args
        await backup.backup(backup, ctx)
        patched_create_backup.assert_called()

    ctx.typing.assert_called()
    ctx.message.reply.assert_called()
    backup_file: File = ctx.message.reply.call_args.kwargs["file"]
    assert isinstance(backup_file, File)
    assert backup_file.filename.endswith(".backup.tar.gz")
    ctx.message.remove_reaction.assert_called_with("⏳", ctx.me)
    ctx.message.add_reaction.assert_called_with("✅")


async def test_error():
    backup = BackupCog()
    ctx = AsyncMock(spec=Context)
    ctx.message = AsyncMock(spec=Message)
    with patch(
        "cogs.backup.backup.create_backup",
        side_effect=Exception("test exception from create_backup"),
    ) as patched_create_backup:
        with raises(Exception, match="test exception from create_backup"):
            # pylint: disable-next=too-many-function-args
            await backup.backup(backup, ctx)
        patched_create_backup.assert_called()
    ctx.typing.assert_called()
    ctx.message.reply.assert_called_with("Backup failed, please see log.")
    ctx.message.remove_reaction.assert_called_with("⏳", ctx.me)
    ctx.message.add_reaction.assert_called_with("❌")
