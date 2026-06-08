from dataclasses import dataclass
import logging
from typing import Optional
import re
from redbot.core import commands, Config
import discord
import ibis
from . import rules

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
                        "* Must contain only letters, numbers, hyphens, underscores, periods, and "
                        + "spaces",
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

    async def add_member_to_thread(
        self, thread: discord.Thread, member: discord.Member
    ):
        try:
            await thread.add_user(member)
        # pylint: disable-next=broad-exception-caught
        except Exception as ex:
            _log.exception(
                "Could not add user %s to thread %s.",
                member.name,
                thread.jump_url,
                exc_info=ex,
            )
            await thread.send(f"Could not add user {member.name}")

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
                # Note: ForumChannels do not currently support private threads
                thread = (
                    await channel.create_thread(
                        name=title,
                        allowed_mentions=discord.AllowedMentions.none(),
                        content=content,
                    )
                ).thread
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

        await self.add_member_to_thread(thread, interaction.user)

        for responder in self.config.responders:
            match responder:
                case discord.Member() as member:
                    await self.add_member_to_thread(thread, member)
                case discord.Role() as role:
                    for member in role.members:
                        await self.add_member_to_thread(thread, member)
                case _:
                    _log.error(
                        "Tried to add unknown object %s (%s) to thread %s.",
                        type(responder),
                        responder,
                        thread.jump_url,
                    )

        return thread

    # pylint: disable-next=arguments-differ
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

    # pylint: disable-next=arguments-differ
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
    ) -> list[discord.Member | discord.Role]:
        return [
            responder
            for responder in [
                guild.get_member(id) or guild.get_role(id)
                for id in await self.config.guild(guild).responders()
            ]
            if responder
        ]

    async def set_responders(
        self, guild: discord.Guild, responders: list[discord.Member | discord.Role]
    ):
        await self.config.guild(guild).responders.set(
            [responder.id for responder in responders]
        )

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
            responders = (
                ", ".join(
                    responder.mention
                    for responder in await self.get_responders(ctx.guild)
                )
                or "<no responders>"
            )
            await ibis.reply.success(ctx, f"Current responders: {responders}")

    @namechanger_responders.command(name="add")
    async def namechanger_responders_add(
        self,
        ctx: commands.Context,
        users: commands.Greedy[discord.Member | discord.Role],
    ):
        """Add responders for name changes."""
        if not users:
            await ibis.reply.fail(
                ctx,
                "No responders provided, or I cannot see any of the members or roles you "
                + "mentioned.",
            )
            return

        current_responders = await self.get_responders(ctx.guild)
        new_responders = list(set(current_responders + users))

        if current_responders == new_responders:
            await ibis.reply.fail(
                ctx,
                "All of the members or roles provided were already marked as responders.",
            )
            return

        await self.set_responders(ctx.guild, new_responders)
        await self.apply_prompts(ctx.guild)
        await ibis.reply.success(ctx)

    @namechanger_responders.command(name="remove")
    async def namechanger_responders_remove(
        self,
        ctx: commands.Context,
        users: commands.Greedy[discord.Member | discord.Role],
    ):
        """Remove responders for name changes."""
        if not users:
            await ibis.reply.fail(
                ctx,
                "No responders provided, or I cannot see any of the members or roles you "
                + "mentioned.",
            )
            return

        current_responders = await self.get_responders(ctx.guild)
        new_responders = list(set(current_responders) - set(users))

        if current_responders == new_responders:
            await ibis.reply.fail(
                ctx, "None of the members or roles provided were marked as responders."
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
