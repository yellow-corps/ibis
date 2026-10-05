from typing import Optional
import logging
from redbot.core import commands, Config
import discord
import ibis

_log = logging.getLogger(__name__)


class AutoTaggerCog(commands.Cog):
    def __init__(self):
        self.config = Config.get_conf(
            self, identifier=301473723569536906, force_registration=True
        )

        self.config.register_channel(
            **{"enabled": False, "off_tag": None, "on_tag": None, "exclude_tag": None}
        )

    async def load_channel_tags(
        self, channel: discord.ForumChannel, config: Optional[dict] = None
    ) -> Optional[
        tuple[discord.ForumTag, discord.ForumTag, Optional[discord.ForumTag]]
    ]:
        config = config if config else await self.config.channel(channel).all()

        if not config["enabled"]:
            return None

        off_tag, on_tag, exclude_tag = (
            channel.get_tag(tag_id)
            for tag_id in [config["off_tag"], config["on_tag"], config["exclude_tag"]]
        )

        if not off_tag or not on_tag or (config["exclude_tag"] and not exclude_tag):
            _log.warning(
                "A tag was possibly deleted? channel=%s, off_tag=%s, on_tag=%s, exclude_tag=%s",
                channel,
                config["off_tag"],
                config["on_tag"],
                config["exclude_tag"],
            )
            return None

        return off_tag, on_tag, exclude_tag

    @commands.group()
    @commands.admin()
    @commands.guild_only()
    async def autotagger(self, ctx: commands.Context):
        """Auto Tagger"""

    @autotagger.command(name="list")
    async def autotagger_list(self, ctx: commands.Context):
        """List configured autotaggers in this guild."""

        output = []

        for channel_id, config in (await self.config.all_channels()).items():
            channel = ctx.guild.get_channel(channel_id)
            if not channel or not config["enabled"]:
                continue

            tags = await self.load_channel_tags(channel, config)

            if not tags:
                output.append(
                    f"- {channel.mention}: A configured tag has been deleted, please enable again."
                )
                continue

            off_tag, on_tag, exclude_tag = tags
            exclude_tag_name = exclude_tag.name if exclude_tag else "`None`"
            output.append(
                f"- {channel.mention}: "
                + ", ".join(
                    [
                        f"`off_tag`={off_tag.name}",
                        f"`on_tag`={on_tag.name}",
                        f"`exclude_tag`={exclude_tag_name}",
                    ]
                )
            )

        if not output:
            await ibis.reply.success(ctx, "No autotaggers configured.")
            return

        await ibis.reply.success(ctx, "\n".join(["Configured autotaggers:", *output]))

    @autotagger.command(name="enable")
    # pylint: disable-next=too-many-arguments,too-many-positional-arguments
    async def autotagger_enable(
        self,
        ctx: commands.Context,
        channel: discord.ForumChannel,
        off_tag_name: str,
        on_tag_name: str,
        exclude_tag_name: Optional[str],
    ):
        """Sets up a forum channel to automatically tag threads."""

        if not channel.permissions_for(ctx.me).manage_threads:
            await ibis.reply.fail(
                ctx,
                f"Bot requires `Manage Threads` permission on {channel.mention} first.",
            )
            return

        tag_names = [
            name.lower() if name else None
            for name in (off_tag_name, on_tag_name, exclude_tag_name)
        ]

        if len(set(tag_names)) != 3:
            await ibis.reply.fail(ctx, "Cannot use the same tags for off/on/exclude.")
            return

        available_tags_by_name = {
            tag.name.lower(): tag for tag in channel.available_tags
        }
        off_tag, on_tag, exclude_tag = (
            available_tags_by_name.get(tag_name) for tag_name in tag_names
        )

        if not off_tag:
            await ibis.reply.fail(ctx, f"Could not find tag {off_tag_name}.")
            return

        if not on_tag:
            await ibis.reply.fail(ctx, f"Could not find tag {on_tag_name}.")
            return

        if not exclude_tag and exclude_tag_name:
            await ibis.reply.fail(ctx, f"Could not find tag {exclude_tag_name}.")
            return

        try:
            await self.config.channel(channel).set(
                {
                    "enabled": True,
                    "off_tag": off_tag.id,
                    "on_tag": on_tag.id,
                    "exclude_tag": exclude_tag.id if exclude_tag else None,
                }
            )
            await ibis.reply.success(ctx)
        # pylint: disable-next=broad-exception-caught
        except Exception as ex:
            await ibis.reply.fail(
                ctx, "Could not apply autotagging settings to channel."
            )
            _log.exception(
                "Could not apply autotagging settings to channel.", exc_info=ex
            )

    @autotagger.command("disable")
    async def autotagger_disable(
        self, ctx: commands.Context, channel: discord.ForumChannel
    ):
        """Removes a previously configured auto tagging configuration."""
        try:
            await self.config.channel(channel).clear()
            await ibis.reply.success(ctx)
        # pylint: disable-next=broad-exception-caught
        except Exception as ex:
            await ibis.reply.fail(
                ctx, "Could not clear autotagging settings from channel."
            )
            _log.exception(
                "Could not clear autotagging settings from channel.", exc_info=ex
            )

    @commands.Cog.listener()
    async def on_thread_create(self, thread: discord.Thread):
        try:
            await self.update(None, thread)
        # pylint: disable-next=broad-exception-caught
        except Exception as ex:
            _log.exception("Could not autotag thread %s", thread, exc_info=ex)

    @commands.Cog.listener()
    async def on_thread_update(self, before: discord.Thread, after: discord.Thread):
        try:
            await self.update(before, after)
        # pylint: disable-next=broad-exception-caught
        except Exception as ex:
            _log.exception("Could not autotag thread %s", after, exc_info=ex)

    async def update(
        self, before_thread: Optional[discord.Thread], thread: discord.Thread
    ):
        if thread.archived:
            return

        channel = thread.parent
        if not isinstance(channel, discord.ForumChannel):
            return

        tags = await self.load_channel_tags(channel)
        if not tags:
            return

        off_tag, on_tag, exclude_tag = tags
        all_tags = {tag for tag in tags if tag}

        async def add(tag: discord.ForumTag):
            if tag not in thread.applied_tags:
                await thread.add_tags(tag, reason="autotagger")

        async def remove(tag: discord.ForumTag):
            if tag in thread.applied_tags:
                await thread.remove_tags(tag, reason="autotagger")

        before = set(before_thread.applied_tags if before_thread else []) & all_tags
        after = set(thread.applied_tags) & all_tags

        if exclude_tag in after:
            return

        if before == after:  # no tags changed
            if not after:  # neither tag defined
                await add(off_tag)
            return

        added_tags = after - before
        removed_tags = before - after

        if on_tag in added_tags:
            await remove(off_tag)
        elif off_tag in added_tags:
            await remove(on_tag)
        elif on_tag in removed_tags:
            await add(off_tag)
        elif off_tag in removed_tags:
            await add(on_tag)
        elif exclude_tag in removed_tags and not after:
            await add(off_tag)
