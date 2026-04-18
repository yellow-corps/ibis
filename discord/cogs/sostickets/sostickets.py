import re
from functools import reduce
from typing import Union
from io import StringIO
from redbot.core import commands, Config
import yaml
from jsonschema import ValidationError
import discord
import ibis
from .modals import SosTicketsPrompt
from .schema import PromptsConfig


class SosTicketsException(Exception):
    pass


class SosTickets(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.config = Config.get_conf(
            self, identifier=249419295041331774, force_registration=True
        )
        self.bot = bot

        default_guild = {
            "enabled": False,
            "channel": {"name": None, "next_no": 1},
            "category": {"active": None, "archive": None},
            "export": {"channel": None, "auto_prune": False},
            "motd": None,
            "responders": [],
            "prompts_config": "",
        }

        self.config.register_guild(**default_guild)

        self.handling_sos = False
        self.current_prompts: dict[int, SosTicketsPrompt] = {}

    async def get_enabled(self, guild: discord.Guild) -> bool:
        return await self.config.guild(guild).enabled()

    async def set_enabled(self, guild: discord.Guild, enabled: bool):
        await self.config.guild(guild).enabled.set(enabled)

    async def get_channel_name(self, guild: discord.Guild) -> str:
        return await self.config.guild(guild).channel.name()

    async def set_channel_name(self, guild: discord.Guild, name: str):
        await self.config.guild(guild).channel.name.set(name)

    async def is_active_channel(self, channel: discord.TextChannel) -> bool:
        name = await self.get_channel_name(channel.guild)
        if not channel.name.startswith(name):
            return False
        name_regex = re.compile(f"^{re.escape(name)}-\\d+$")
        return name_regex.match(channel.name)

    async def is_start_channel(self, channel: discord.TextChannel) -> bool:
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

    async def get_prompts_config(self, guild: discord.Guild) -> dict:
        return yaml.load(
            await self.config.guild(guild).prompts_config(), Loader=yaml.Loader
        )

    async def set_prompts_config(self, guild: discord.Guild, config: dict):
        await self.config.guild(guild).prompts_config.set(
            yaml.dump(config, Dumper=yaml.Dumper)
        )

    async def create_start_channel(self, guild: discord.Guild):
        name = await self.get_channel_name(guild)
        channel = await guild.create_text_channel(
            name=name,
            category=await self.get_active_category(guild),
            position=0,
            reason="SosTickets: recreating start channel",
        )
        motd = await self.get_motd(guild)
        prompt = self.current_prompts.get(guild.id)
        if motd or prompt:
            await channel.send(content=motd, view=prompt, silent=True)

    async def use_start_channel(self, guild: discord.Guild):
        name = await self.get_channel_name(guild)
        channel = next(
            (channel for channel in guild.channels if channel.name == name), None
        )
        if not channel:
            raise SosTicketsException(f"Channel `#{name}` does not exist in {guild}")

        next_no = await self.get_channel_next_no(guild)
        next_name = f"{name}-{next_no}"

        async with channel.typing():
            await channel.edit(
                name=next_name,
                position=next_no,
                reason="SosTickets: creating new ticket",
            )
            await self.set_channel_next_no(guild, next_no + 1)

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            await self.apply_prompts_config(guild)

    async def cog_load(self):
        for guild in self.bot.guilds:
            await self.apply_prompts_config(guild)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if (
            message.author.bot
            or self.current_prompts.get(message.guild.id)
            or not isinstance(message.channel, discord.TextChannel)
            or not await self.is_start_channel(message.channel)
            or self.handling_sos
        ):
            return

        self.handling_sos = True
        try:
            await self.use_start_channel(message.guild)
            await self.create_start_channel(message.guild)
            responders = await self.get_responders(message.guild)
            if responders:
                await message.reply(" ".join(u.mention for u in responders))
            else:
                await message.add_reaction("✅")
        finally:
            self.handling_sos = False

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
            await ibis.reply.fail(
                ctx,
                "Must set up channel name, active category, and archive category first.",
            )
            return

        try:
            await self.create_start_channel(ctx.guild)
        except Exception as ex:
            await ibis.reply.fail(
                ctx,
                f"Could not create #{await self.get_channel_name(ctx.guild)} channel.",
            )
            raise ex

        await self.rescan_next_no(ctx.guild)
        await self.set_channel_next_no(ctx.guild, True)
        await ibis.reply.success(ctx)

    @sostickets.command(name="disable")
    async def sostickets_disable(self, ctx: commands.Context):
        """Disable SOS tickets from running in this server."""
        await self.set_enabled(ctx.guild, False)
        await ibis.reply.success(
            ctx, "You may want to delete the existing SOS tickets channel."
        )

    async def disable_if_enabled(self, message: discord.Message):
        if await self.get_enabled(message.guild):
            await self.set_enabled(message.guild, False)
            await message.reply(
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
            await ibis.reply.success(ctx, f"Current SOS channel: {channel}")
        else:
            await self.set_channel_name(ctx.guild, channel)
            await ibis.reply.success(ctx)
            await self.disable_if_enabled(ctx)

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
            await ibis.reply.success(ctx, f"The active SOS category is: {category}")
        else:
            await self.set_active_category(ctx.guild, category)
            await ibis.reply.success(ctx)
            await self.disable_if_enabled(ctx.message)

    @sostickets_category.command(name="archive")
    async def sostickets_category_archive(
        self, ctx: commands.Context, category: discord.CategoryChannel = None
    ):
        """Gets or sets the archive SOS category"""
        if not category:
            category = await self.get_archive_category(ctx.guild) or "<no category>"
            await ibis.reply.success(ctx, f"The archive SOS category is: {category}")
        else:
            await self.set_archive_category(ctx.guild, category)
            await ibis.reply.success(ctx)
            await self.disable_if_enabled(ctx.message)

    @sostickets.group(name="export", autohelp=False)
    async def sostickets_export(self, ctx: commands.Context):
        """Configures archived SOS tickets exporting functionality"""
        if not ctx.invoked_subcommand:
            channel = await self.get_export_channel(ctx.guild)
            channel = channel.mention if channel else "<no channel>"
            auto_prune = await self.get_export_auto_prune(ctx.guild)
            await ibis.reply.success(
                ctx,
                f"Current export channel: {channel}, auto pruning: {auto_prune}",
            )

    @sostickets_export.command(name="set")
    async def sostickets_export_set(
        self, ctx: commands.Context, channel: discord.TextChannel
    ):
        """Set the channel to export SOS tickets to."""
        await self.set_export_channel(ctx.guild, channel)
        await ibis.reply.success(ctx)

    @sostickets_export.command(name="clear")
    async def sostickets_export_clear(self, ctx: commands.Context):
        """Clear the channel to export SOS tickets to."""
        await self.set_export_channel(ctx.guild, None)
        await ibis.reply.success(ctx)

    @sostickets_export.command(name="auto_prune")
    async def sostickets_export_auto_prune(
        self, ctx: commands.Context, auto_prune: bool
    ):
        """Enable or disable auto pruning of SOS tickets when they're resolved."""
        await self.set_export_auto_prune(ctx.guild, auto_prune)
        await ibis.reply.success(ctx)

    @sostickets.command(name="motd")
    async def sostickets_motd(
        self,
        ctx: commands.Context,
        *,
        content: str = None,
    ):
        """Get or set the "Message Of The Day" to repost into the SOS ticket channel."""
        if not content:
            await ibis.reply.success(ctx, "Current motd for the SOS channel:")
            await ctx.reply(await self.get_motd(ctx.guild) or "<no motd>")
        else:
            await self.set_motd(ctx.guild, content)
            await ibis.reply.success(ctx)

    @sostickets.group(name="responders", autohelp=False)
    async def sostickets_responders(self, ctx: commands.Context):
        """Add or remove responders for SOS tickets."""
        if not ctx.invoked_subcommand:
            users = (
                ", ".join(u.mention for u in await self.get_responders(ctx.guild))
                or "<no responders>"
            )
            await ibis.reply.success(ctx, f"Current responders: {users}")

    @sostickets_responders.command(name="add")
    async def sostickets_responders_add(
        self,
        ctx: commands.Context,
        users: commands.Greedy[Union[discord.User, discord.Role]],
    ):
        """Add responders for SOS tickets."""
        if not users:
            await ibis.reply.fail(
                ctx,
                "No responders provided or I cannot see any of the users you mentioned.",
            )
            return

        current_responders = await self.get_responders(ctx.guild)
        new_responders = list(set(current_responders + users))

        if current_responders == new_responders:
            await ibis.reply.fail(
                ctx,
                "All of the users provided were already marked as responders.",
            )
            return

        await self.set_responders(ctx.guild, new_responders)
        await ibis.reply.success(ctx)

    @sostickets_responders.command(name="remove")
    async def sostickets_responders_remove(
        self,
        ctx: commands.Context,
        users: commands.Greedy[Union[discord.User, discord.Role]],
    ):
        """Remove responders for SOS tickets."""
        if not users:
            await ibis.reply.fail(
                ctx,
                "No users provided or I cannot see any of the users you mentioned.",
            )
            return

        current_responders = await self.get_responders(ctx.guild)
        new_responders = list(set(current_responders) - set(users))

        if current_responders == new_responders:
            await ibis.reply.fail(
                ctx, "None of the users provided were marked as responders."
            )
            return

        await self.set_responders(ctx.guild, new_responders)
        await ibis.reply.success(ctx)

    @sostickets.group("prompts-config")
    async def sostickets_prompts_config(self, ctx: commands.Context):
        """Add or remove a prompts configuration for SOS tickets."""

    @sostickets_prompts_config.command("get")
    async def sostickets_prompts_config_get(self, ctx: commands.Context):
        """View a current prompts configuration for SOS tickets."""

        prompts_config = await self.get_prompts_config(ctx.guild)

        if prompts_config:
            file = discord.File(
                fp=StringIO(yaml.dump(prompts_config, Dumper=yaml.Dumper)),
                filename="prompts-config.yaml",
            )
            await ibis.reply.success(
                ctx.message, "Current prompts config is attached", file=file
            )
        else:
            await ibis.reply.success(
                ctx.message, "No prompts config is defined currently"
            )

    @sostickets_prompts_config.command("set")
    async def sostickets_prompts_config_set(self, ctx: commands.Context):
        """Add a prompts configuration for SOS tickets."""
        async with ctx.typing():
            for attachment in ctx.message.attachments:
                if attachment.filename.endswith(".yml") or attachment.filename.endswith(
                    ".yaml"
                ):
                    try:
                        config = yaml.load(await attachment.read(), Loader=yaml.Loader)
                        PromptsConfig.validate(config)
                        await self.set_prompts_config(ctx.guild, config)
                    except yaml.YAMLError as exc:
                        await ibis.reply.fail(
                            ctx.message, f"Attachment did not contain valid YAML: {exc}"
                        )
                    except ValidationError as exc:
                        await ibis.reply.fail(
                            ctx.message,
                            f"Attachment did not validate against expected YAML schema: {exc}",
                        )
                    await self.apply_prompts_config(ctx.guild)
                    await ibis.reply.success(ctx.message)
                    return
        await ibis.reply.fail(
            ctx.message,
            "You must attach a `.yaml` file to your message to set the config",
        )

    @sostickets_prompts_config.command("clear")
    async def sostickets_prompts_config_clear(self, ctx: commands.Context):
        """Clear a prompts configuration for SOS tickets."""
        await self.set_prompts_config(ctx.guild, {})
        await self.apply_prompts_config(ctx.guild)

    async def export_channel(self, channel: discord.TextChannel):
        export_channel = await self.get_export_channel(channel.guild)
        if not export_channel:
            return

        await channel.send(f"Attempting to export channel to {export_channel.mention}.")

        try:
            html_file = await ibis.export.channel(
                channel,
                "html",
            )
            text_file = await ibis.export.channel(
                channel,
                "text",
            )

            await export_channel.send(
                f"Exported ticket `#{channel.name}`.", files=[html_file, text_file]
            )
        except Exception as ex:
            await channel.send(
                "Attempted to export channel but an error occurred. Will not export or prune."
            )
            raise ex

    async def prune_channel(self, channel: discord.TextChannel):
        try:
            await channel.delete(reason="pruning SOS ticket")
        except Exception as ex:
            await channel.send(
                "Attempted to prune channel but an error occurred. Will not prune."
            )
            raise ex

    @sostickets.command(name="resolve")
    async def sostickets_resolve(self, ctx: commands.Context):
        """Mark an SOS ticket as resolved, archiving it, and auto-pruning it if enabled."""
        if not await self.is_active_channel(ctx.channel):
            await ibis.reply.fail(ctx, "This is not an active SOS tickets channel.")
            return

        if ctx.channel.category != await self.get_active_category(ctx.guild):
            await ibis.reply.fail(
                ctx,
                "This SOS ticket is not located in the active SOS tickets category.",
            )
            return

        async with ctx.typing():
            await ctx.channel.move(
                category=await self.get_archive_category(ctx.guild),
                sync_permissions=True,
                end=True,
                reason="ticket resolved",
            )
            await ibis.reply.success(ctx, "Channel archived.")

        if await self.get_export_auto_prune(ctx.channel.guild):
            async with ctx.typing():
                await self.export_channel(ctx.channel)
                await self.prune_channel(ctx.channel)

    @sostickets.command(name="prune")
    async def sostickets_prune(self, ctx: commands.Context):
        """Prune a resolved and archived SOS ticket"""
        if not await self.is_active_channel(ctx.channel):
            await ibis.reply.fail(ctx, "This is not an active SOS tickets channel.")
            return

        if ctx.channel.category != await self.get_archive_category(ctx.guild):
            await ibis.reply.fail(
                ctx,
                "This SOS ticket is not located in the archive SOS tickets category.",
            )
            return

        async with ctx.typing():
            await self.export_channel(ctx.channel)
            await self.prune_channel(ctx.channel)

    async def apply_prompts_config(self, guild: discord.Guild):
        async def create_channel(
            message: str, files: list[discord.File]
        ) -> discord.Message:
            name = await self.get_channel_name(guild)
            next_no = await self.get_channel_next_no(guild)
            next_name = f"{name}-{next_no}"

            channel = await guild.create_text_channel(
                name=next_name,
                category=await self.get_active_category(guild),
                position=next_no,
                reason="SosTickets: creating new ticket",
            )
            message = await channel.send(content=message, files=files)
            await self.set_channel_next_no(guild, next_no + 1)
            return message

        prompts_config = await self.get_prompts_config(guild)
        self.current_prompts[guild.id] = (
            SosTicketsPrompt(prompts_config, create_channel) if prompts_config else None
        )
        if self.current_prompts[guild.id]:
            self.bot.add_view(self.current_prompts[guild.id])
