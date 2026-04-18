from dataclasses import dataclass, field
from typing import Optional, Any
from enum import Enum
from pathlib import Path
import yaml
import jsonschema
import discord


class ModalItemType(str, Enum):
    TEXT = "text"
    PARAGRAPH = "paragraph"
    SELECT = "select"
    FILE = "file"
    NOTE = "note"


@dataclass
class SelectOption:
    value: str
    label: str
    emoji: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SelectOption":
        value = f'{data["emoji"]} {data["label"]}' if "emoji" in data else data["label"]
        return cls(
            value=value,
            label=data["label"],
            emoji=data.get("emoji"),
        )


@dataclass
class ModalItem:
    item_id: int
    label: str
    description: Optional[str] = None
    type: ModalItemType = ModalItemType.TEXT
    required: bool = True
    options: list[SelectOption] = field(default_factory=list)

    @classmethod
    def from_dict(cls, item_id: int, data: dict[str, Any]) -> "ModalItem":
        options = [SelectOption.from_dict(opt) for opt in data.get("options", [])]
        return cls(
            item_id=item_id,
            label=data["label"],
            description=data.get("description"),
            type=ModalItemType(data.get("type", "text")),
            required=data.get("required", True),
            options=options,
        )


@dataclass
class Assignee:
    def as_mention(self, guild: discord.Guild) -> str:
        raise NotImplementedError


@dataclass
class UserAssignee(Assignee):
    user: str

    def as_mention(self, guild: discord.Guild) -> str:
        return getattr(
            discord.utils.get(guild.members, name=self.user), "mention", self.user
        )


@dataclass
class RoleAssignee(Assignee):
    role: str

    def as_mention(self, guild: discord.Guild) -> str:
        return getattr(
            discord.utils.get(guild.roles, name=self.role), "mention", self.role
        )


@dataclass
class Prompt:
    prompt_id: str
    full_title: str
    title: str
    emoji: Optional[str] = None
    accent: Optional[str] = None
    assignees: list[Assignee] = field(default_factory=list)
    items: list[ModalItem] = field(default_factory=list)
    followup: Optional[str] = None

    @classmethod
    def from_dict(cls, prompt_id: str, data: dict[str, Any]) -> "Prompt":
        full_title = (
            f'{data["emoji"]} {data["title"]}' if "emoji" in data else data["title"]
        )

        items = [
            ModalItem.from_dict(index, item) for index, item in enumerate(data["items"])
        ]

        assignees = []
        for assignee in data["assignees"]:
            match assignee:
                case {"user": name}:
                    assignees.append(UserAssignee(name))
                case {"role": name}:
                    assignees.append(RoleAssignee(name))

        return cls(
            prompt_id=prompt_id,
            full_title=full_title,
            title=data["title"],
            emoji=data.get("emoji"),
            items=items,
            assignees=assignees,
            accent=data.get("accent"),
            followup=data.get("followup"),
        )


@dataclass
class PromptsConfig:
    prompts: list[Prompt] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PromptsConfig":
        PromptsConfig.validate(data)
        prompts = [Prompt.from_dict(id, data) for id, data in data["prompts"].items()]
        return cls(prompts=prompts)

    @classmethod
    def validate(cls, data: dict[str, Any]):
        with open(
            Path(__file__).with_name("schema.yaml"),
            "r",
            encoding="utf-8",
        ) as schema:
            jsonschema.validate(
                instance=data, schema=yaml.load(schema, Loader=yaml.Loader)
            )
