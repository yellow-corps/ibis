import logging
from datetime import datetime
from typing import Any, Protocol
import discord
from .schema import PromptsConfig, Prompt, ModalItemType

_log = logging.getLogger(__name__)


class SosTicketsCallback(Protocol):
    async def __call__(
        self, message: str, files: list[discord.File]
    ) -> discord.Message: ...


class SosTicketsPrompt(discord.ui.View):

    def __init__(
        self,
        prompt_config: dict[str, Any],
        callback: SosTicketsCallback,
    ):
        super().__init__(timeout=None)

        prompt_config = PromptsConfig.from_dict(prompt_config)

        for prompt in prompt_config.prompts:
            self.add_item(SosTicketsButton(prompt, callback))


class SosTicketsButton(discord.ui.Button):

    def __init__(self, prompt: Prompt, create_callback: SosTicketsCallback):
        super().__init__()
        self.custom_id = prompt.prompt_id
        self.label = prompt.title
        self.emoji = prompt.emoji
        self.prompt = prompt
        self.create_callback = create_callback

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(
            SosTicketsModal(self.prompt, self.create_callback)
        )


class SosTicketsModal(discord.ui.Modal, title=""):

    def __init__(self, prompt: Prompt, callback: SosTicketsCallback):
        super().__init__()
        self.title = prompt.full_title
        self.prompt = prompt
        self.callback = callback
        for item in prompt.items:
            match item.type:
                case ModalItemType.TEXT:
                    self.add_item(
                        discord.ui.Label(
                            text=item.label,
                            description=item.description,
                            component=discord.ui.TextInput(
                                id=item.item_id, required=item.required
                            ),
                        )
                    )
                case ModalItemType.PARAGRAPH:
                    self.add_item(
                        discord.ui.Label(
                            text=item.label,
                            description=item.description,
                            component=discord.ui.TextInput(
                                id=item.item_id,
                                required=item.required,
                                style=discord.TextStyle.paragraph,
                            ),
                        )
                    )
                case ModalItemType.SELECT:
                    self.add_item(
                        discord.ui.Label(
                            text=item.label,
                            description=item.description,
                            component=discord.ui.Select(
                                id=item.item_id,
                                options=[
                                    discord.SelectOption(
                                        label=option.label,
                                        value=option.value,
                                        emoji=option.emoji,
                                    )
                                    for option in item.options
                                ],
                            ),
                        )
                    )
                case ModalItemType.FILE:
                    self.add_item(
                        discord.ui.Label(
                            description=item.description,
                            text=item.label,
                            component=discord.ui.FileUpload(
                                id=item.item_id, required=item.required
                            ),
                        )
                    )
                case ModalItemType.NOTE:
                    self.add_item(
                        discord.ui.TextDisplay(id=item.item_id, content=item.label)
                    )
                case _:
                    raise ValueError(f'Unknown `type` of "{item.type}" provided.')

    async def on_submit(self, interaction: discord.Interaction):
        message = await self.callback(
            "\n".join(self.format_response(interaction)),
            await self.files(),
        )
        await interaction.response.send_message(
            f"Your submission was received. [Click here to view it.]({message.jump_url})",
            ephemeral=True,
        )

    async def on_error(
        self, interaction: discord.Interaction, error: Exception
    ) -> None:
        await interaction.response.send_message(
            "Something went wrong and your submission was not received. Please try again.",
            ephemeral=True,
        )

        # Make sure we know what the error actually is
        _log.exception("Something went wrong handling a submission", exc_info=error)

    async def files(self) -> list[discord.File]:
        files: list[discord.File] = []
        for item in self.children:
            if not isinstance(item, discord.ui.Label):
                continue

            component = item.component
            match component:
                case discord.ui.FileUpload():
                    for file in component.values:
                        files.append(await file.to_file())

        return files

    def format_response(self, interaction: discord.Interaction):
        yield f"# {self.prompt.full_title}"
        yield f"Reported at {discord.utils.format_dt(datetime.now())}"
        yield "## Reported by"
        yield interaction.user.mention
        yield "## Assigned to"
        yield ", ".join(
            [
                assignee.as_mention(interaction.guild)
                for assignee in self.prompt.assignees
            ]
        )
        yield "-# ~~                                ~~"
        yield from self.format_children()
        yield "-# ~~                                ~~"

        if self.prompt.followup:
            yield self.prompt.followup

    def format_children(self):
        for item in self.children:
            if not isinstance(item, discord.ui.Label):
                continue

            label = item.text
            component = item.component
            match component:
                case discord.ui.TextInput():
                    yield f"## {label}"
                    yield component.value
                case discord.ui.Select():
                    yield f"## {label}"
                    yield ", ".join(component.values)
