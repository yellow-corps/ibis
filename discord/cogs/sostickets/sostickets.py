import re
from functools import reduce
from typing import Union
from io import BytesIO
from redbot.core import commands, Config
from aiohttp import ClientSession
import discord


class SosTicketsException(Exception):
    pass


class SosTickets(commands.Cog):
    def __init__(self):
        self.config = Config.get_conf(
            self, identifier=249419295041331774, force_registration=True
        )

        default_guild = {
            "enabled": False,
            "channel": {"name": None, "next_no": 1},
            "category": {"active": None, "archive": None},
            "export": {"channel": None, "auto_prune": False},
            "motd": None,
            "responders": [],
        }

        self.config.register_guild(**default_guild)

        self.handling_sos = False

    async def get_enabled(self, guild: discord.Guild) -> bool:
        return await self.config.guild(guild).enabled()

    async def set_enabled(self, guild: discord.Guild, enabled: bool):
        await self.config.guild(guild).enabled.set(enabled)

    async def get_channel_name(self, guild: discord.Guild) -> str:
        return await self.config.guild(guild).channel.name()

    async def set_channel_name(self, guild: discord.Guild, name: str):
        await self.config.guild(guild).channel.name.set(name)

    async def is_active_channel(self, channel: discord.TextChannel):
        name = await self.get_channel_name(channel.guild)
        if not channel.name.startswith(name):
            return False
        name_regex = re.compile(f"^{re.escape(name)}-\\d+$")
        return name_regex.match(channel.name)

    async def is_start_channel(self, channel: discord.TextChannel):
        return channel.name == await self.get_channel_name(channel.guild)

    async def get_channel_next_no(self, guild: discord.Guild) -> int:
        return int(await self.config.guild(guild).channel.next_no())

    async def set_channel_next_no(self, guild: discord.Guild, next_no: int):
        await self.config.guild(guild).channel.next_no.set(next_no)

    async def rescan_next_no(self, guild: discord.Guild):
        name = await self.get_channel_name(guild)
        name_regex = re.compile(f"^{re.escape(name)}-(\\d+)$")
        channels = [
            channel for channel in guild.channels if name_regex.match(channel.name)
        ]
        next_no = reduce(
            lambda acc, cur: max(acc, int(name_regex.match(cur.name).group(1))),
            channels,
            1,
        )
        await self.set_channel_next_no(guild, next_no)

    async def get_active_category(
        self, guild: discord.Guild
    ) -> discord.CategoryChannel:
        return guild.get_channel(await self.config.guild(guild).category.active())

    async def set_active_category(
        self, guild: discord.Guild, category: Union[discord.CategoryChannel]
    ):
        await self.config.guild(guild).category.active.set(
            category if isinstance(category, int) else category.id
        )

    async def get_archive_category(
        self, guild: discord.Guild
    ) -> discord.CategoryChannel:
        return guild.get_channel(await self.config.guild(guild).category.archive())

    async def set_archive_category(
        self, guild: discord.Guild, category: Union[discord.CategoryChannel]
    ):
        await self.config.guild(guild).category.archive.set(
            category if isinstance(category, int) else category.id
        )

    async def get_export_channel(self, guild: discord.Guild) -> discord.TextChannel:
        return guild.get_channel(await self.config.guild(guild).export.channel())

    async def set_export_channel(
        self, guild: discord.Guild, channel: discord.TextChannel
    ):
        await self.config.guild(guild).export.channel.set(channel.id)

    async def get_export_auto_prune(self, guild: discord.Guild) -> bool:
        return await self.config.guild(guild).export.auto_prune()

    async def set_export_auto_prune(self, guild: discord.Guild, auto_prune: bool):
        await self.config.guild(guild).export.auto_prune.set(auto_prune)

    async def get_motd(self, guild: discord.Guild) -> str:
        return await self.config.guild(guild).motd()

    async def set_motd(self, guild: discord.Guild, motd: str):
        await self.config.guild(guild).motd.set(motd)

    async def get_responders(
        self, guild: discord.Guild
    ) -> list[Union[discord.User, discord.Role]]:
        return [
            guild.get_member(id) or guild.get_role(id)
            for id in await self.config.guild(guild).responders()
        ]

    async def set_responders(
        self, guild: discord.Guild, users: list[Union[discord.User, discord.Role]]
    ):
        await self.config.guild(guild).responders.set([u.id for u in users])

    async def create_start_channel(self, guild: discord.Guild):
        name = await self.get_channel_name(guild)
        channel = await guild.create_text_channel(
            name=name,
            category=await self.get_active_category(guild),
            position=0,
            reason="ticket created",
        )
        motd = await self.get_motd(guild)
        if motd:
            await channel.send(content=motd, silent=True)

    async def use_start_channel(self, guild: discord.Guild):
        name = await self.get_channel_name(guild)
        channel = next(
            (channel for channel in guild.channels if channel.name == name), None
        )
        if not channel:
            raise SosTicketsException(f"Channel `#{name}` does not exist in {guild}")

        next_no = await self.get_channel_next_no(guild)
        next_name = f"{name}-{next_no}"
        await channel.edit(name=next_name, position=next_no, reason="moving ticket")
        await self.set_channel_next_no(guild, next_no + 1)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if (
            self.handling_sos
            or message.author.bot
            or not await self.is_start_channel(message.channel)
        ):
            return

        self.handling_sos = True
        try:
            await self.use_start_channel(message.guild)
            await self.create_start_channel(message.guild)
            await message.reply(
                " ".join(u.mention for u in await self.get_responders(message.guild))
            )
        finally:
            self.handling_sos = False

    async def reply_success(self, message: discord.Message, reply: str = None):
        if reply:
            await message.reply(reply)
        await message.add_reaction("✅")

    async def reply_fail(self, message: discord.Message, reply: str):
        await message.reply(reply)
        await message.add_reaction("❌")

    @commands.group()
    @commands.admin()
    @commands.guild_only()
    async def sostickets(self, ctx: commands.Context):
        """SOS tickets"""

    @sostickets.command(name="enable")
    async def sostickets_enable(self, ctx: commands.Context):
        """Enable SOS tickets to run in this server."""
        if (
            not await self.get_channel_name(ctx.guild)
            or not await self.get_active_category(ctx.guild)
            or not await self.get_archive_category(ctx.guild)
        ):
            return await self.reply_fail(
                ctx.message,
                "Must set up channel name, active category, and archive category first.",
            )
        try:
            await self.create_start_channel(ctx.guild)
        except Exception as ex:
            await self.reply_fail(
                ctx.message,
                f"Could not create #{await self.get_channel_name(ctx.guild)} channel.",
            )
            raise ex

        await self.rescan_next_no(ctx.guild)
        await self.set_channel_next_no(ctx.guild, True)
        await self.reply_success(ctx.message)

    @sostickets.command(name="disable")
    async def sostickets_disable(self, ctx: commands.Context):
        """Disable SOS tickets from running in this server."""
        await self.set_enabled(ctx.guild, False)
        await self.reply_success(
            ctx.message, "You may want to delete the existing SOS tickets channel."
        )

    async def disable_if_enabled(self, message: discord.Message):
        if await self.get_enabled(message.guild):
            await self.set_enabled(message.guild, False)
            return await message.reply(
                " ".join(
                    [
                        "SOS Tickets disabled as configuration was changed.",
                        "Please re-enable using `[@] sostickets enable`",
                    ]
                )
            )

    @sostickets.command(name="channel")
    async def sostickets_channel(self, ctx: commands.Context, channel: str = None):
        """Get or set the SOS ticket channel to use."""
        if not channel:
            channel = await self.get_channel_name(ctx.guild) or "<no channel>"
            await self.reply_success(ctx.message, f"Current SOS channel: {channel}")
        else:
            await self.set_channel_name(ctx.guild, channel)
            await self.reply_success(ctx.message)
            await self.disable_if_enabled(ctx.message)

    @sostickets.group(name="category")
    async def sostickets_category(self, ctx: commands.Context):
        """Get or set SOS categories"""

    @sostickets_category.command(name="active")
    async def sostickets_category_active(
        self, ctx: commands.Context, category: discord.CategoryChannel = None
    ):
        """Gets or sets the active SOS category"""
        if not category:
            category = await self.get_active_category(ctx.guild) or "<no category>"
            await self.reply_success(
                ctx.message, f"The active SOS category is: {category}"
            )
        else:
            await self.set_active_category(ctx.guild, category)
            await self.reply_success(ctx.message)
            await self.disable_if_enabled(ctx.message)

    @sostickets_category.command(name="archive")
    async def sostickets_category_archive(
        self, ctx: commands.Context, category: discord.CategoryChannel = None
    ):
        """Gets or sets the archive SOS category"""
        if not category:
            category = await self.get_archive_category(ctx.guild) or "<no category>"
            await self.reply_success(
                ctx.message, f"The archive SOS category is: {category}"
            )
        else:
            await self.set_archive_category(ctx.guild, category)
            await self.reply_success(ctx.message)
            await self.disable_if_enabled(ctx.message)

    @sostickets.group(name="export", autohelp=False)
    async def sostickets_export(self, ctx: commands.Context):
        """Configures archived SOS tickets exporting functionality"""
        if not ctx.invoked_subcommand:
            export_channel = (
                await self.get_export_channel(ctx.guild)
            ).mention or "<no channel>"
            export_auto_prune = await self.get_export_auto_prune(ctx.guild)
            await self.reply_success(
                ctx.message,
                f"Current export channel: {export_channel}, auto pruning: {export_auto_prune}",
            )

    @sostickets_export.command(name="set")
    async def sostickets_export_set(
        self, ctx: commands.Context, channel: discord.TextChannel
    ):
        """Set the channel to export SOS tickets to."""
        await self.set_export_channel(ctx.guild, channel)
        await self.reply_success(ctx.message)

    @sostickets_export.command(name="clear")
    async def sostickets_export_clear(self, ctx: commands.Context):
        """Clear the channel to export SOS tickets to."""
        await self.set_export_channel(ctx.guild, None)
        await self.reply_success(ctx.message)

    @sostickets_export.command(name="auto_prune")
    async def sostickets_export_auto_prune(
        self, ctx: commands.Context, auto_prune: bool
    ):
        """Enable or disable auto pruning of SOS tickets when they're resolved."""
        await self.set_export_auto_prune(ctx.guild, auto_prune)
        await self.reply_success(ctx.message)

    @sostickets.command(name="motd")
    async def sostickets_motd(
        self,
        ctx: commands.Context,
        *,
        content: str = None,
    ):
        """Get or set the "Message Of The Day" to repost into the SOS ticket channel."""
        if not content:
            await self.reply_success(ctx.message, "Current motd for the SOS channel:")
            await ctx.reply(await self.get_motd(ctx.guild) or "<no motd>")
        else:
            await self.set_motd(ctx.guild, content)
            await self.reply_success(ctx.message)

    @sostickets.group(name="responders", autohelp=False)
    async def sostickets_responders(self, ctx: commands.Context):
        """Add or remove responders for SOS tickets."""
        if not ctx.invoked_subcommand:
            users = (
                ", ".join(u.mention for u in await self.get_responders(ctx.guild))
                or "<no responders>"
            )
            await self.reply_success(ctx.message, f"Current responders: {users}")

    @sostickets_responders.command(name="add")
    async def sostickets_responders_add(
        self,
        ctx: commands.Context,
        users: commands.Greedy[Union[discord.User, discord.Role]],
    ):
        """Add responders for SOS tickets."""
        if not users:
            return await self.reply_fail(
                ctx.message,
                "No responders provided or I cannot see any of the users you mentioned.",
            )

        current_responders = await self.get_responders(ctx.guild)
        new_responders = list(set(current_responders + users))

        if current_responders == new_responders:
            return await self.reply_fail(
                ctx.message,
                "All of the users provided were already marked as responders.",
            )

        await self.set_responders(ctx.guild, new_responders)
        await self.reply_success(ctx.message)

    @sostickets_responders.command(name="remove")
    async def sostickets_responders_remove(
        self,
        ctx: commands.Context,
        users: commands.Greedy[Union[discord.User, discord.Role]],
    ):
        """Remove responders for SOS tickets."""
        if not users:
            return await self.reply_fail(
                ctx.message,
                "No users provided or I cannot see any of the users you mentioned.",
            )

        current_responders = await self.get_responders(ctx.guild)
        new_responders = list(set(current_responders) - set(users))

        if current_responders == new_responders:
            return await self.reply_fail(
                ctx.message, "None of the users provided were marked as responders."
            )

        await self.set_responders(ctx.guild, new_responders)
        await self.reply_success(ctx.message)

    async def do_export(
        self, channel: discord.TextChannel, bot: commands.Bot, file_format: str
    ) -> discord.File:
        file_ext = "zip" if file_format == "html" else "txt"
        url = f"http://localhost:8081/channel/{channel.id}/{file_ext}?botName={bot.user.name}"
        print(f"GET {url}")
        async with ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    raise SosTicketsException(
                        f"Attempted to export channel, but got a {response.status} HTTP status."
                    )
                return discord.File(
                    fp=BytesIO(await response.read()),
                    filename=f"{channel.name}.{file_format}.{file_ext}",
                )

    async def export_channel(self, channel: discord.TextChannel, bot: commands.Bot):
        export_channel = await self.get_export_channel(channel.guild)
        if not export_channel:
            return

        await channel.send(f"Attempting to export channel to {export_channel.mention}.")

        html_file = await self.do_export(channel, bot, "html")
        text_file = await self.do_export(channel, bot, "text")

        await export_channel.send(
            f"Exported ticket `#{channel.name}`.", files=[html_file, text_file]
        )

    async def prune_channel(self, channel: discord.TextChannel):
        if await self.get_export_auto_prune(channel.guild):
            try:
                await channel.delete(reason="auto prune enabled")
            except Exception as ex:
                await channel.send("Attempted to prune channel but an error occurred.")
                raise ex

    @sostickets.command(name="resolve")
    async def sostickets_resolve(self, ctx: commands.Context):
        """Mark an SOS ticket as resolved, archiving it."""
        if not await self.is_active_channel(ctx.channel):
            return await self.reply_fail(
                ctx.message, "This is not an active SOS tickets channel."
            )

        await ctx.channel.move(
            category=await self.get_archive_category(ctx.guild),
            sync_permissions=True,
            end=True,
            reason="ticket resolved",
        )
        await self.reply_success(ctx.message, "Channel archived.")
        await self.export_channel(ctx.channel, ctx.bot)
        await self.prune_channel(ctx.channel)
