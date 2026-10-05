from typing import Optional
from unittest import mock
import logging
import pytest
from redbot.core.config import Config, Group
from redbot.core.commands import Context
from discord import ForumChannel, ForumTag, Guild, TextChannel, Thread
from .autotagger import AutoTaggerCog


def _tag(tag_id: int, name: str) -> mock.Mock:
    tag = mock.Mock(ForumTag)
    tag.id = tag_id
    tag.name = name
    return tag


off_tag = _tag(1, "off")
on_tag = _tag(2, "on")
exclude_tag = _tag(3, "exclude")
other_tag = _tag(4, "other")
UNKNOWN_TAG_NAME = "unknown"


def _channel(channel_id: int = 100) -> mock.Mock:
    channel = mock.Mock(ForumChannel)
    channel.id = channel_id
    channel.mention = f"<#{channel_id}>"
    channel.available_tags = [off_tag, on_tag, exclude_tag, other_tag]
    channel.permissions_for.return_value.manage_threads = True

    def get_tag(tag_id: Optional[int]) -> Optional[ForumTag]:
        return {tag.id: tag for tag in channel.available_tags}.get(tag_id)

    channel.get_tag.side_effect = get_tag
    return channel


def _thread(parent: mock.Mock, applied_tags: list[ForumTag]) -> mock.AsyncMock:
    thread = mock.AsyncMock(Thread)
    thread.archived = False
    thread.parent = parent
    thread.applied_tags = applied_tags
    return thread


def _cog() -> AutoTaggerCog:
    cog = AutoTaggerCog()
    cog.config = mock.Mock(Config)
    cog.config.channel.return_value = mock.Mock(Group)
    return cog


# enable


@pytest.mark.asyncio
async def test_enable_missing_permission():
    cog = _cog()

    ctx = mock.AsyncMock(Context)
    channel = _channel()
    channel.permissions_for.return_value.manage_threads = False

    with (
        mock.patch("ibis.reply.fail") as mock_fail,
        mock.patch("ibis.reply.success") as mock_success,
    ):
        # pylint: disable-next=too-many-function-args
        await cog.autotagger_enable(cog, ctx, channel, off_tag.name, on_tag.name, None)

        channel.permissions_for.assert_called_once_with(ctx.me)
        mock_fail.assert_awaited_once_with(
            ctx, f"Bot requires `Manage Threads` permission on {channel.mention} first."
        )
        mock_success.assert_not_awaited()
        cog.config.channel.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    argnames=("off_tag_name", "on_tag_name", "exclude_tag_name"),
    argvalues=[
        (off_tag.name, off_tag.name, None),
        (off_tag.name, on_tag.name, off_tag.name),
        (off_tag.name, on_tag.name, on_tag.name),
        (off_tag.name.upper(), off_tag.name, None),
    ],
)
async def test_enable_duplicate_tags(
    off_tag_name: str, on_tag_name: str, exclude_tag_name: Optional[str]
):
    cog = _cog()

    ctx = mock.AsyncMock(Context)
    channel = _channel()

    with (
        mock.patch("ibis.reply.fail") as mock_fail,
        mock.patch("ibis.reply.success") as mock_success,
    ):
        # pylint: disable-next=too-many-function-args
        await cog.autotagger_enable(
            cog, ctx, channel, off_tag_name, on_tag_name, exclude_tag_name
        )

        mock_fail.assert_awaited_once_with(
            ctx, "Cannot use the same tags for off/on/exclude."
        )
        mock_success.assert_not_awaited()
        cog.config.channel.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    argnames=("off_tag_name", "on_tag_name", "exclude_tag_name"),
    argvalues=[
        (UNKNOWN_TAG_NAME, on_tag.name, None),
        (off_tag.name, UNKNOWN_TAG_NAME, None),
        (off_tag.name, on_tag.name, UNKNOWN_TAG_NAME),
    ],
)
async def test_enable_unknown_tag(
    off_tag_name: str, on_tag_name: str, exclude_tag_name: Optional[str]
):
    cog = _cog()

    ctx = mock.AsyncMock(Context)
    channel = _channel()

    with (
        mock.patch("ibis.reply.fail") as mock_fail,
        mock.patch("ibis.reply.success") as mock_success,
    ):
        # pylint: disable-next=too-many-function-args
        await cog.autotagger_enable(
            cog, ctx, channel, off_tag_name, on_tag_name, exclude_tag_name
        )

        mock_fail.assert_awaited_once_with(ctx, "Could not find tag unknown.")
        mock_success.assert_not_awaited()
        cog.config.channel.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    argnames=("off_tag_name", "on_tag_name", "exclude_tag_name"),
    argvalues=[
        (off_tag.name, on_tag.name, None),
        (off_tag.name, on_tag.name, exclude_tag.name),
        (off_tag.name.upper(), on_tag.name.title(), exclude_tag.name.upper()),
    ],
)
async def test_enable_success(
    off_tag_name: str, on_tag_name: str, exclude_tag_name: Optional[str]
):
    cog = _cog()

    ctx = mock.AsyncMock(Context)
    channel = _channel()

    with (
        mock.patch("ibis.reply.fail") as mock_fail,
        mock.patch("ibis.reply.success") as mock_success,
    ):
        # pylint: disable-next=too-many-function-args
        await cog.autotagger_enable(
            cog, ctx, channel, off_tag_name, on_tag_name, exclude_tag_name
        )

        cog.config.channel.assert_called_once_with(channel)
        cog.config.channel.return_value.set.assert_awaited_once_with(
            {
                "enabled": True,
                "off_tag": off_tag.id,
                "on_tag": on_tag.id,
                "exclude_tag": exclude_tag.id if exclude_tag_name else None,
            }
        )
        mock_success.assert_awaited_once_with(ctx)
        mock_fail.assert_not_awaited()


@pytest.mark.asyncio
async def test_enable_failed_saving_config(caplog: pytest.LogCaptureFixture):
    cog = _cog()
    cog.config.channel.return_value.set.side_effect = Exception("config write failed")

    ctx = mock.AsyncMock(Context)
    channel = _channel()

    with (
        mock.patch("ibis.reply.fail") as mock_fail,
        mock.patch("ibis.reply.success") as mock_success,
    ):
        # pylint: disable-next=too-many-function-args
        await cog.autotagger_enable(cog, ctx, channel, off_tag.name, on_tag.name, None)

        cog.config.channel.assert_called_once_with(channel)
        cog.config.channel.return_value.set.assert_awaited_once()
        mock_fail.assert_awaited_once_with(
            ctx, "Could not apply autotagging settings to channel."
        )
        mock_success.assert_not_awaited()
        assert (
            "autotagger.autotagger",
            logging.ERROR,
            "Could not apply autotagging settings to channel.",
        ) in caplog.record_tuples


# disable


@pytest.mark.asyncio
async def test_disable_success():
    cog = _cog()

    ctx = mock.AsyncMock(Context)
    channel = _channel()

    with (
        mock.patch("ibis.reply.fail") as mock_fail,
        mock.patch("ibis.reply.success") as mock_success,
    ):
        # pylint: disable-next=too-many-function-args
        await cog.autotagger_disable(cog, ctx, channel)

        cog.config.channel.assert_called_once_with(channel)
        cog.config.channel.return_value.clear.assert_awaited_once_with()
        mock_success.assert_awaited_once_with(ctx)
        mock_fail.assert_not_awaited()


@pytest.mark.asyncio
async def test_disable_failed_saving_config(caplog: pytest.LogCaptureFixture):
    cog = _cog()
    cog.config.channel.return_value.clear.side_effect = Exception("config clear failed")

    ctx = mock.AsyncMock(Context)
    channel = _channel()

    with (
        mock.patch("ibis.reply.fail") as mock_fail,
        mock.patch("ibis.reply.success") as mock_success,
    ):
        # pylint: disable-next=too-many-function-args
        await cog.autotagger_disable(cog, ctx, channel)

        cog.config.channel.assert_called_once_with(channel)
        cog.config.channel.return_value.clear.assert_awaited_once()
        mock_fail.assert_awaited_once_with(
            ctx, "Could not clear autotagging settings from channel."
        )
        mock_success.assert_not_awaited()
        assert (
            "autotagger.autotagger",
            logging.ERROR,
            "Could not clear autotagging settings from channel.",
        ) in caplog.record_tuples


# list


@pytest.mark.asyncio
async def test_list_none_configured():
    cog = _cog()
    cog.config.all_channels.return_value = {}

    ctx = mock.AsyncMock(Context)

    with (
        mock.patch("ibis.reply.fail") as mock_fail,
        mock.patch("ibis.reply.success") as mock_success,
    ):
        # pylint: disable-next=too-many-function-args
        await cog.autotagger_list(cog, ctx)

        cog.config.all_channels.assert_awaited_once()
        mock_success.assert_awaited_once_with(ctx, "No autotaggers configured.")
        mock_fail.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    argnames=("channel_found", "enabled"),
    argvalues=[
        (False, True),  # deleted, or in another guild
        (True, False),
    ],
)
async def test_list_skips_unavailable(channel_found: bool, enabled: bool):
    cog = _cog()

    ctx = mock.AsyncMock(Context)
    ctx.guild = mock.Mock(Guild)
    channel = _channel()

    guild_channels = {channel.id: channel} if channel_found else {}
    ctx.guild.get_channel.side_effect = guild_channels.get
    cog.config.all_channels.return_value = {
        channel.id: {
            "enabled": enabled,
            "off_tag": off_tag.id,
            "on_tag": on_tag.id,
            "exclude_tag": None,
        }
    }

    with (
        mock.patch("ibis.reply.fail") as mock_fail,
        mock.patch("ibis.reply.success") as mock_success,
    ):
        # pylint: disable-next=too-many-function-args
        await cog.autotagger_list(cog, ctx)

        mock_success.assert_awaited_once_with(ctx, "No autotaggers configured.")
        mock_fail.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    argnames="deleted_tag", argvalues=[off_tag, on_tag, exclude_tag]
)
async def test_list_tag_deleted(deleted_tag: ForumTag):
    cog = _cog()

    ctx = mock.AsyncMock(Context)
    ctx.guild = mock.Mock(Guild)
    channel = _channel()
    channel.available_tags.remove(deleted_tag)

    guild_channels = {channel.id: channel}
    ctx.guild.get_channel.side_effect = guild_channels.get
    cog.config.all_channels.return_value = {
        channel.id: {
            "enabled": True,
            "off_tag": off_tag.id,
            "on_tag": on_tag.id,
            "exclude_tag": exclude_tag.id,
        }
    }

    with (
        mock.patch("ibis.reply.fail") as mock_fail,
        mock.patch("ibis.reply.success") as mock_success,
    ):
        # pylint: disable-next=too-many-function-args
        await cog.autotagger_list(cog, ctx)

        mock_success.assert_awaited_once_with(
            ctx,
            "Configured autotaggers:\n"
            + f"- {channel.mention}: A configured tag has been deleted, please enable again.",
        )
        mock_fail.assert_not_awaited()


@pytest.mark.asyncio
async def test_list_success():
    cog = _cog()

    ctx = mock.AsyncMock(Context)
    ctx.guild = mock.Mock(Guild)
    channel = _channel(1)
    excluding_channel = _channel(2)

    guild_channels = {channel.id: channel, excluding_channel.id: excluding_channel}
    ctx.guild.get_channel.side_effect = guild_channels.get
    cog.config.all_channels.return_value = {
        channel.id: {
            "enabled": True,
            "off_tag": off_tag.id,
            "on_tag": on_tag.id,
            "exclude_tag": None,
        },
        excluding_channel.id: {
            "enabled": True,
            "off_tag": off_tag.id,
            "on_tag": on_tag.id,
            "exclude_tag": exclude_tag.id,
        },
    }

    with (
        mock.patch("ibis.reply.fail") as mock_fail,
        mock.patch("ibis.reply.success") as mock_success,
    ):
        # pylint: disable-next=too-many-function-args
        await cog.autotagger_list(cog, ctx)

        mock_success.assert_awaited_once_with(
            ctx,
            "Configured autotaggers:\n"
            + f"- {channel.mention}: `off_tag`=off, `on_tag`=on, `exclude_tag`=`None`\n"
            + f"- {excluding_channel.mention}: `off_tag`=off, `on_tag`=on, `exclude_tag`=exclude",
        )
        mock_fail.assert_not_awaited()


# load_channel_tags


@pytest.mark.asyncio
async def test_load_channel_tags_not_enabled():
    cog = _cog()
    cog.config.channel.return_value.all = mock.AsyncMock(
        return_value={
            "enabled": False,
            "off_tag": off_tag.id,
            "on_tag": on_tag.id,
            "exclude_tag": exclude_tag.id,
        }
    )

    channel = _channel()

    tags = await cog.load_channel_tags(channel)

    assert tags is None
    cog.config.channel.assert_called_once_with(channel)
    cog.config.channel.return_value.all.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    argnames="deleted_tag", argvalues=[off_tag, on_tag, exclude_tag]
)
async def test_load_channel_tags_tag_deleted(
    caplog: pytest.LogCaptureFixture, deleted_tag: ForumTag
):
    cog = _cog()
    cog.config.channel.return_value.all = mock.AsyncMock(
        return_value={
            "enabled": True,
            "off_tag": off_tag.id,
            "on_tag": on_tag.id,
            "exclude_tag": exclude_tag.id,
        }
    )

    channel = _channel()
    channel.available_tags.remove(deleted_tag)

    tags = await cog.load_channel_tags(channel)

    assert tags is None
    assert (
        "autotagger.autotagger",
        logging.WARNING,
        f"A tag was possibly deleted? channel={channel}, off_tag={off_tag.id}, "
        + f"on_tag={on_tag.id}, exclude_tag={exclude_tag.id}",
    ) in caplog.record_tuples


@pytest.mark.asyncio
@pytest.mark.parametrize(
    argnames="configured_exclude_tag", argvalues=[None, exclude_tag]
)
async def test_load_channel_tags_success(configured_exclude_tag: Optional[ForumTag]):
    cog = _cog()
    cog.config.channel.return_value.all = mock.AsyncMock(
        return_value={
            "enabled": True,
            "off_tag": off_tag.id,
            "on_tag": on_tag.id,
            "exclude_tag": (
                configured_exclude_tag.id if configured_exclude_tag else None
            ),
        }
    )

    channel = _channel()

    tags = await cog.load_channel_tags(channel)

    assert tags == (off_tag, on_tag, configured_exclude_tag)


@pytest.mark.asyncio
async def test_load_channel_tags_uses_given_config():
    cog = _cog()
    cog.config.channel.return_value.all = mock.AsyncMock(
        return_value={
            "enabled": False,
            "off_tag": None,
            "on_tag": None,
            "exclude_tag": None,
        }
    )

    channel = _channel()

    tags = await cog.load_channel_tags(
        channel,
        {
            "enabled": True,
            "off_tag": off_tag.id,
            "on_tag": on_tag.id,
            "exclude_tag": exclude_tag.id,
        },
    )

    assert tags == (off_tag, on_tag, exclude_tag)
    cog.config.channel.assert_not_called()
    cog.config.channel.return_value.all.assert_not_awaited()


# listeners


@pytest.mark.asyncio
async def test_thread_create():
    cog = _cog()
    cog.config.channel.return_value.all = mock.AsyncMock(
        return_value={
            "enabled": True,
            "off_tag": off_tag.id,
            "on_tag": on_tag.id,
            "exclude_tag": exclude_tag.id,
        }
    )

    channel = _channel()
    # both tags, so off_tag is only removed if the listener passes before=None
    thread = _thread(channel, [off_tag, on_tag])

    await cog.on_thread_create(thread)

    thread.add_tags.assert_not_awaited()
    thread.remove_tags.assert_awaited_once_with(off_tag, reason="autotagger")


@pytest.mark.asyncio
async def test_thread_create_logs_exception(caplog: pytest.LogCaptureFixture):
    cog = _cog()
    cog.config.channel.return_value.all = mock.AsyncMock(
        return_value={
            "enabled": True,
            "off_tag": off_tag.id,
            "on_tag": on_tag.id,
            "exclude_tag": exclude_tag.id,
        }
    )

    channel = _channel()
    thread = _thread(channel, [])
    thread.add_tags.side_effect = Exception("add tags failed")

    await cog.on_thread_create(thread)

    thread.add_tags.assert_awaited_once()
    assert (
        "autotagger.autotagger",
        logging.ERROR,
        f"Could not autotag thread {thread}",
    ) in caplog.record_tuples


@pytest.mark.asyncio
async def test_thread_update():
    cog = _cog()
    cog.config.channel.return_value.all = mock.AsyncMock(
        return_value={
            "enabled": True,
            "off_tag": off_tag.id,
            "on_tag": on_tag.id,
            "exclude_tag": exclude_tag.id,
        }
    )

    channel = _channel()
    # only (before, after) sees off_tag as newly added, and so removes on_tag
    before = _thread(channel, [on_tag])
    after = _thread(channel, [on_tag, off_tag])

    await cog.on_thread_update(before, after)

    after.add_tags.assert_not_awaited()
    after.remove_tags.assert_awaited_once_with(on_tag, reason="autotagger")


@pytest.mark.asyncio
async def test_thread_update_logs_exception(caplog: pytest.LogCaptureFixture):
    cog = _cog()
    cog.config.channel.return_value.all = mock.AsyncMock(
        return_value={
            "enabled": True,
            "off_tag": off_tag.id,
            "on_tag": on_tag.id,
            "exclude_tag": exclude_tag.id,
        }
    )

    channel = _channel()
    before = _thread(channel, [])
    after = _thread(channel, [])
    after.add_tags.side_effect = Exception("add tags failed")

    await cog.on_thread_update(before, after)

    after.add_tags.assert_awaited_once()
    assert (
        "autotagger.autotagger",
        logging.ERROR,
        f"Could not autotag thread {after}",
    ) in caplog.record_tuples


# update guards


@pytest.mark.asyncio
async def test_update_archived():
    cog = _cog()
    cog.config.channel.return_value.all = mock.AsyncMock(
        return_value={
            "enabled": True,
            "off_tag": off_tag.id,
            "on_tag": on_tag.id,
            "exclude_tag": exclude_tag.id,
        }
    )

    channel = _channel()
    thread = _thread(channel, [])
    thread.archived = True

    await cog.update(None, thread)

    thread.add_tags.assert_not_awaited()
    thread.remove_tags.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_not_forum_channel():
    cog = _cog()
    cog.config.channel.return_value.all = mock.AsyncMock(
        return_value={
            "enabled": True,
            "off_tag": off_tag.id,
            "on_tag": on_tag.id,
            "exclude_tag": exclude_tag.id,
        }
    )

    channel = mock.Mock(TextChannel)
    thread = _thread(channel, [])

    await cog.update(None, thread)

    cog.config.channel.assert_not_called()
    thread.add_tags.assert_not_awaited()
    thread.remove_tags.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_not_enabled():
    cog = _cog()
    cog.config.channel.return_value.all = mock.AsyncMock(
        return_value={
            "enabled": False,
            "off_tag": off_tag.id,
            "on_tag": on_tag.id,
            "exclude_tag": exclude_tag.id,
        }
    )

    channel = _channel()
    thread = _thread(channel, [])

    await cog.update(None, thread)

    thread.add_tags.assert_not_awaited()
    thread.remove_tags.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    argnames="deleted_tag", argvalues=[off_tag, on_tag, exclude_tag]
)
async def test_update_tag_deleted(deleted_tag: ForumTag):
    cog = _cog()
    cog.config.channel.return_value.all = mock.AsyncMock(
        return_value={
            "enabled": True,
            "off_tag": off_tag.id,
            "on_tag": on_tag.id,
            "exclude_tag": exclude_tag.id,
        }
    )

    channel = _channel()
    channel.available_tags.remove(deleted_tag)
    thread = _thread(channel, [])

    await cog.update(None, thread)

    thread.add_tags.assert_not_awaited()
    thread.remove_tags.assert_not_awaited()


# update tagging
# before=None is a newly created thread (on_thread_create)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    argnames=("before", "after", "added", "removed"),
    argvalues=[
        (None, [], off_tag, None),
        ([], [], off_tag, None),
        ([other_tag], [other_tag], off_tag, None),
    ],
)
async def test_update_tags_untagged(
    before: Optional[list[ForumTag]],
    after: list[ForumTag],
    added: Optional[ForumTag],
    removed: Optional[ForumTag],
):
    cog = _cog()
    cog.config.channel.return_value.all = mock.AsyncMock(
        return_value={
            "enabled": True,
            "off_tag": off_tag.id,
            "on_tag": on_tag.id,
            "exclude_tag": exclude_tag.id,
        }
    )

    channel = _channel()
    before_thread = _thread(channel, before) if before is not None else None
    thread = _thread(channel, after)

    await cog.update(before_thread, thread)

    if added:
        thread.add_tags.assert_awaited_once_with(added, reason="autotagger")
    else:
        thread.add_tags.assert_not_awaited()
    if removed:
        thread.remove_tags.assert_awaited_once_with(removed, reason="autotagger")
    else:
        thread.remove_tags.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    argnames=("before", "after", "added", "removed"),
    argvalues=[
        ([off_tag], [off_tag], None, None),
        ([on_tag], [on_tag], None, None),
        ([off_tag, other_tag], [off_tag], None, None),
        ([on_tag], [on_tag, other_tag], None, None),
    ],
)
async def test_update_tags_unchanged(
    before: Optional[list[ForumTag]],
    after: list[ForumTag],
    added: Optional[ForumTag],
    removed: Optional[ForumTag],
):
    cog = _cog()
    cog.config.channel.return_value.all = mock.AsyncMock(
        return_value={
            "enabled": True,
            "off_tag": off_tag.id,
            "on_tag": on_tag.id,
            "exclude_tag": exclude_tag.id,
        }
    )

    channel = _channel()
    before_thread = _thread(channel, before) if before is not None else None
    thread = _thread(channel, after)

    await cog.update(before_thread, thread)

    if added:
        thread.add_tags.assert_awaited_once_with(added, reason="autotagger")
    else:
        thread.add_tags.assert_not_awaited()
    if removed:
        thread.remove_tags.assert_awaited_once_with(removed, reason="autotagger")
    else:
        thread.remove_tags.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    argnames=("before", "after", "added", "removed"),
    argvalues=[
        (None, [on_tag], None, None),
        (None, [off_tag, on_tag], None, off_tag),
        ([off_tag], [off_tag, on_tag], None, off_tag),
        ([on_tag], [on_tag, off_tag], None, on_tag),
        ([off_tag], [on_tag], None, None),  # swapped in one edit
    ],
)
async def test_update_tags_added(
    before: Optional[list[ForumTag]],
    after: list[ForumTag],
    added: Optional[ForumTag],
    removed: Optional[ForumTag],
):
    cog = _cog()
    cog.config.channel.return_value.all = mock.AsyncMock(
        return_value={
            "enabled": True,
            "off_tag": off_tag.id,
            "on_tag": on_tag.id,
            "exclude_tag": exclude_tag.id,
        }
    )

    channel = _channel()
    before_thread = _thread(channel, before) if before is not None else None
    thread = _thread(channel, after)

    await cog.update(before_thread, thread)

    if added:
        thread.add_tags.assert_awaited_once_with(added, reason="autotagger")
    else:
        thread.add_tags.assert_not_awaited()
    if removed:
        thread.remove_tags.assert_awaited_once_with(removed, reason="autotagger")
    else:
        thread.remove_tags.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    argnames=("before", "after", "added", "removed"),
    argvalues=[
        ([on_tag], [], off_tag, None),
        ([off_tag], [], on_tag, None),
    ],
)
async def test_update_tags_removed(
    before: Optional[list[ForumTag]],
    after: list[ForumTag],
    added: Optional[ForumTag],
    removed: Optional[ForumTag],
):
    cog = _cog()
    cog.config.channel.return_value.all = mock.AsyncMock(
        return_value={
            "enabled": True,
            "off_tag": off_tag.id,
            "on_tag": on_tag.id,
            "exclude_tag": exclude_tag.id,
        }
    )

    channel = _channel()
    before_thread = _thread(channel, before) if before is not None else None
    thread = _thread(channel, after)

    await cog.update(before_thread, thread)

    if added:
        thread.add_tags.assert_awaited_once_with(added, reason="autotagger")
    else:
        thread.add_tags.assert_not_awaited()
    if removed:
        thread.remove_tags.assert_awaited_once_with(removed, reason="autotagger")
    else:
        thread.remove_tags.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    argnames=("before", "after", "added", "removed"),
    argvalues=[
        ([off_tag, on_tag], [on_tag], None, None),  # after removing off_tag
        ([on_tag, off_tag], [off_tag], None, None),  # after removing on_tag
        ([], [off_tag], None, None),  # after adding off_tag
        ([], [on_tag], None, None),  # after adding on_tag
    ],
)
async def test_update_tags_follow_up_no_op(
    before: Optional[list[ForumTag]],
    after: list[ForumTag],
    added: Optional[ForumTag],
    removed: Optional[ForumTag],
):
    cog = _cog()
    cog.config.channel.return_value.all = mock.AsyncMock(
        return_value={
            "enabled": True,
            "off_tag": off_tag.id,
            "on_tag": on_tag.id,
            "exclude_tag": exclude_tag.id,
        }
    )

    channel = _channel()
    before_thread = _thread(channel, before) if before is not None else None
    thread = _thread(channel, after)

    await cog.update(before_thread, thread)

    if added:
        thread.add_tags.assert_awaited_once_with(added, reason="autotagger")
    else:
        thread.add_tags.assert_not_awaited()
    if removed:
        thread.remove_tags.assert_awaited_once_with(removed, reason="autotagger")
    else:
        thread.remove_tags.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    argnames=("before", "after", "added", "removed"),
    argvalues=[
        ([], [exclude_tag], None, None),
        ([off_tag], [off_tag, exclude_tag], None, None),
        ([exclude_tag], [exclude_tag], None, None),
        ([exclude_tag], [], off_tag, None),
        ([exclude_tag, off_tag], [off_tag], None, None),
        ([exclude_tag, on_tag], [on_tag], None, None),
        ([exclude_tag, on_tag], [exclude_tag], None, None),
        ([exclude_tag, off_tag], [exclude_tag, off_tag, on_tag], None, None),
    ],
)
async def test_update_tags_exclude(
    before: Optional[list[ForumTag]],
    after: list[ForumTag],
    added: Optional[ForumTag],
    removed: Optional[ForumTag],
):
    cog = _cog()
    cog.config.channel.return_value.all = mock.AsyncMock(
        return_value={
            "enabled": True,
            "off_tag": off_tag.id,
            "on_tag": on_tag.id,
            "exclude_tag": exclude_tag.id,
        }
    )

    channel = _channel()
    before_thread = _thread(channel, before) if before is not None else None
    thread = _thread(channel, after)

    await cog.update(before_thread, thread)

    if added:
        thread.add_tags.assert_awaited_once_with(added, reason="autotagger")
    else:
        thread.add_tags.assert_not_awaited()
    if removed:
        thread.remove_tags.assert_awaited_once_with(removed, reason="autotagger")
    else:
        thread.remove_tags.assert_not_awaited()
