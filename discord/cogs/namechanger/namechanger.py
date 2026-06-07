from redbot.core import commands, Config
import discord
from dataclasses import dataclass
import logging
from typing import Protocol, Optional
from . import rules
import re
import ibis

_log = logging.getLogger(__name__)


class NameChangerException(Exception):
    pass


@dataclass
class NameChangerPromptConfig:
    responders: list[discord.Member | discord.Role]


class NameChangerPrompt(discord.ui.View):

    def __init__(self, config: NameChangerPromptConfig):
        super().__init__(timeout=None)

        self.add_item(NameChangerButton(config))


class NameChangerButton(discord.ui.Button):
    def __init__(self, config: NameChangerPromptConfig):
        super().__init__()
        self.custom_id = "namechanger_button"
        self.label = "Request to change your Handle"
        self.emoji = "🪪"
        self.style = discord.ButtonStyle.green
        self.config = config

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(NameChangerModal(self.config))


@dataclass
class NameChangeData:
    current_handle: str
    new_handle: str
    notes: Optional[str] = None


class NameChangerModal(discord.ui.Modal, title=""):
    def __init__(self, config: NameChangerPromptConfig):
        super().__init__()
        self.config = config
        self.title = "🪪 Request to change your Handle"

        self.add_item(
            discord.ui.TextDisplay(
                content="\n".join(
                    [
                        "# Handle Requirements",
                        "* 3 to 20 characters",
                        "* Must contain letters, numbers, hyphens, underscores, periods, and spaces",
                        "* Must be unique",
                        "* No swear words or slurs",
                        "* All handle change requests will be subject to final approval",
                        "# Request",
                    ]
                )
            )
        )

        self.add_item(
            discord.ui.Label(
                text="Current Handle",
                component=discord.ui.TextInput(
                    custom_id="current_handle", required=True
                ),
            )
        )

        self.add_item(
            discord.ui.Label(
                text="New Handle",
                component=discord.ui.TextInput(custom_id="new_handle", required=True),
            )
        )

        self.add_item(
            discord.ui.Label(
                text="Notes",
                component=discord.ui.TextInput(
                    custom_id="notes", style=discord.TextStyle.paragraph, required=False
                ),
            )
        )

    def parse_data(self) -> NameChangeData:
        data: dict[str, str] = {}
        for item in self.children:
            if not isinstance(item, discord.ui.Label):
                continue

            match item.component:
                case discord.ui.TextInput():
                    data[item.component.custom_id] = item.component.value

        return NameChangeData(**data)

    def format_results(
        self, results: list[rules.ValidationResult], errors_only: bool = False
    ):
        for result in results:
            if result.error or not errors_only:
                yield f"* {result.description}"
                if result.context:
                    yield f"  * {result.context}"

    async def create_post(
        self,
        interaction: discord.Interaction,
        data: NameChangeData,
        results: list[rules.ValidationResult],
    ) -> discord.Thread:
        title = f'Request: "{data.current_handle}" to "{data.new_handle}"'
        content = "\n".join(
            [
                "# Request to change handle",
                "## Requested by",
                interaction.user.mention,
                "## Current handle",
                discord.utils.escape_markdown(data.current_handle),
                "## New handle",
                discord.utils.escape_markdown(data.new_handle),
                *(
                    [
                        "## Notes",
                        *[
                            f"> {discord.utils.escape_markdown(line)}"
                            for line in data.notes.splitlines()
                        ],
                    ]
                    if data.notes
                    else []
                ),
                "## Validation Results",
                *(
                    [
                        f"⚠️ {len(results)} validation issues found!",
                        *self.format_results(results),
                    ]
                    if results
                    else ["✅ No validation issues found!"]
                ),
            ]
        )

        thread: discord.Thread = None
        channel = interaction.channel
        match channel:
            case discord.Thread():
                channel = channel.parent

        match channel:
            case discord.ForumChannel():
                # Note: orumChannels do not currently support private threads
                thread = await channel.create_thread(
                    name=title,
                    allowed_mentions=discord.AllowedMentions.none(),
                    content=content,
                )
            case discord.TextChannel():
                thread = await channel.create_thread(
                    name=title, type=discord.ChannelType.private_thread
                )
                await thread.send(
                    allowed_mentions=discord.AllowedMentions.none(), content=content
                )

            case _:
                raise NameChangerException(
                    f"Current channel is of type {channel.type}, cannot create thread."
                )

        async def add_user_to_thread(user: discord.User):
            try:
                await thread.add_user(user)
            except Exception as ex:
                await thread.send(f"Could not add user {user.name}")
                _log.exception(
                    f"Could not add user {user.name} to thread {thread.jump_url}.",
                    exc_info=ex,
                )

        await add_user_to_thread(interaction.user)

        for responder in self.config.responders:
            match responder:
                case discord.User() as user:
                    await add_user_to_thread(user)
                case discord.Role() as role:
                    for user in role.members:
                        await add_user_to_thread(user)
                case _:
                    _log.error(
                        f"Tried to add unknown object {responder} to thread {thread.jump_url}."
                    )

        return thread

    async def on_submit(self, interaction: discord.Interaction):
        data = self.parse_data()
        split_regex = re.compile(r"(\[|\(|\{)")

        handles = [
            re.split(split_regex, member.display_name)[0]
            for member in interaction.guild.members
            if member.id != interaction.user.id
        ]

        validator = rules.HandleValidator(handles)
        results = validator.validate(data.new_handle)

        if any(result.error for result in results):
            await interaction.response.send_message(
                "\n".join(
                    [
                        f"Your requested new handle, `{data.new_handle}`, has failed validation.",
                        "",
                        "Please address the below issues with your new handle and try again.",
                        *self.format_results(results, errors_only=True),
                    ]
                ),
                ephemeral=True,
            )
            return

        thread = await self.create_post(interaction, data, results)

        await interaction.response.send_message(
            f"Your handle change request was received. [Click here to view it]({thread.jump_url}).",
            ephemeral=True,
        )

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        await interaction.response.send_message(
            "Something went wrong and your submission was not received. Please try again.",
            ephemeral=True,
        )

        _log.exception("Something went wrong handling a submission", exc_info=error)


class NameChanger(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.config = Config.get_conf(
            self, identifier=103476830113429256, force_registration=True
        )
        self.bot = bot

        default_guild = {"responders": []}

        self.config.register_guild(**default_guild)

        self.current_prompts: dict[int, NameChangerPrompt] = {}

    async def get_responders(
        self, guild: discord.Guild
    ) -> list[discord.User | discord.Role]:
        return [
            user
            for user in [
                guild.get_member(id) or guild.get_role(id)
                for id in await self.config.guild(guild).responders()
            ]
            if user
        ]

    async def set_responders(
        self, guild: discord.Guild, users: list[discord.User | discord.Role]
    ):
        await self.config.guild(guild).responders.set([u.id for u in users])

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            await self.apply_prompts(guild)

    async def cog_load(self):
        for guild in self.bot.guilds:
            await self.apply_prompts(guild)

    @commands.group()
    @commands.admin()
    @commands.guild_only()
    async def namechanger(self, ctx: commands.Context):
        """Name Changer"""

    @namechanger.command(name="create")
    async def namechanger_create(
        self,
        ctx: commands.Context,
        channel_or_thread: discord.TextChannel | discord.ForumChannel | discord.Thread,
    ):
        """Creates a Name Changer button in the given thread"""
        match channel_or_thread:
            case discord.TextChannel() as channel:
                await channel.send(view=self.current_prompts.get(channel.guild.id))
            case discord.ForumChannel() as channel:
                await channel.create_thread(
                    name="Request to change your Handle",
                    view=self.current_prompts.get(channel.guild.id),
                )
            case discord.Thread() as thread:
                await thread.send(view=self.current_prompts.get(thread.guild.id))
            case _:
                raise NameChangerException(
                    f"Current channel or thread is of type {channel_or_thread.type}, cannot post."
                )
        await ibis.reply.success(ctx)

    @namechanger.group(name="responders", autohelp=False)
    async def namechanger_responders(self, ctx: commands.Context):
        """Add or remove responders for name changes."""
        if not ctx.invoked_subcommand:
            users = (
                ", ".join(u.mention for u in await self.get_responders(ctx.guild))
                or "<no responders>"
            )
            await ibis.reply.success(ctx, f"Current responders: {users}")

    @namechanger_responders.command(name="add")
    async def namechanger_responders_add(
        self,
        ctx: commands.Context,
        users: commands.Greedy[discord.User | discord.Role],
    ):
        """Add responders for name changes."""
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
        await self.apply_prompts(ctx.guild)
        await ibis.reply.success(ctx)

    @namechanger_responders.command(name="remove")
    async def namechanger_responders_remove(
        self,
        ctx: commands.Context,
        users: commands.Greedy[discord.User | discord.Role],
    ):
        """Remove responders for name changes."""
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
        await self.apply_prompts(ctx.guild)
        await ibis.reply.success(ctx)

    async def apply_prompts(self, guild: discord.Guild):
        self.current_prompts[guild.id] = NameChangerPrompt(
            NameChangerPromptConfig(await self.get_responders(guild))
        )
        self.bot.add_view(self.current_prompts[guild.id])
