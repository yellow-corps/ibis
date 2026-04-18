from io import StringIO
import json
import logging
from redbot.core import commands, Config
from typing_extensions import TypedDict
import discord
import ibis

_log = logging.getLogger(__name__)


class JsonRole(TypedDict):
    name: str
    permissions: dict[str, bool]


class JsonMember(TypedDict):
    username: str
    roles: list[int]


class JsonChannel(TypedDict):
    name: str
    overwrites: dict[str, dict[str, bool]]
    synced: bool


class JsonGuild(TypedDict):
    id: int
    name: str
    roles: dict[str, JsonRole]
    members: dict[str, JsonMember]
    categories: dict[str, JsonChannel]
    channels: dict[str, JsonChannel]


class PermissionsCog(commands.Cog):
    def __init__(self):
        self.config = Config.get_conf(
            self, identifier=778753393002129553, force_registration=True
        )

    @commands.group()
    @commands.admin()
    @commands.guild_only()
    async def permissions(self, ctx: commands.Context):
        """Export and import permissions as JSON objects"""

    @permissions.command(name="import")
    async def permissions_import(self, ctx: commands.Context):
        """Import a permissions object attached to this message into the current guild."""

        if len(ctx.message.attachments) != 1:
            return await ibis.reply.fail(
                ctx,
                f"Expected exactly 1 attachment, found {len(ctx.message.attachments)}",
            )

        attachment = (await ctx.message.attachments[0].read()).decode("utf-8")
        json_guild: JsonGuild = json.loads(attachment)

        if ctx.guild.id != json_guild["id"]:
            return await ibis.reply.fail(
                f"The guild ID `{json_guild['id']}` does not match the current guild"
            )

        failures: list[str] = []

        await ibis.reply.wait(ctx, "Applying role permissions...")
        await self.import_permissions_json_roles(ctx, json_guild, failures)

        await ibis.reply.wait(ctx, "Applying category permissions...")
        await self.import_permissions_json_categories(ctx, json_guild, failures)

        await ibis.reply.wait(ctx, "Applying channel permissions...")
        await self.import_permissions_json_channels(ctx, json_guild, failures)

        if failures:
            failures_str = "\n".join(map(lambda s: f" * {s}", failures))

            await ibis.reply.fail(
                ctx,
                f"Permissions applied with some failures:\n{failures_str}",
            )
        else:
            await ibis.reply.success(ctx, "Permissions applied!")

    async def import_permissions_json_roles(
        self, ctx: commands.Context, json_guild: JsonGuild, failures: list[str]
    ):
        highest_role = ctx.me.roles[-1]
        for json_role_id, json_role in json_guild["roles"].items():
            role = (
                ctx.guild.default_role
                if ctx.guild.default_role.id == int(json_role_id)
                else ctx.guild.get_role(int(json_role_id))
            )

            if role is None:
                failures.append(
                    f"ID `{json_role_id}` did not resolve to a role in this guild"
                )
                continue

            if role >= highest_role:
                failures.append(
                    f"ID `{json_role_id} {role.name}` is equal to or higher than my highest role, so I cannot change it"
                )
                continue

            try:
                role.permissions.update(**json_role["permissions"])
            except Exception as ex:
                failures.append(
                    f"Could not update permissions for role ID {json_role_id}"
                )
                _log.warning(
                    "Could not update permissions for role ID %s",
                    json_role_id,
                    exc_info=ex,
                )

    async def import_permissions_json_categories(
        self, ctx: commands.Context, json_guild: JsonGuild, failures: list[str]
    ):
        for json_category_id, json_category in json_guild["categories"].items():
            category = ctx.guild.get_channel(int(json_category_id))

            if category is None:
                failures.append(
                    f"ID `{json_category_id}` did not resolve to a category channel in this guild"
                )
                continue

            if not isinstance(category, discord.CategoryChannel):
                failures.append(f"ID `{json_category_id}` is not a category channel")
                continue

            for overwrite_id, permissions in json_category["overwrites"].items():
                if not permissions:
                    continue

                overwrite = ctx.guild.get_role(
                    int(overwrite_id)
                ) or ctx.guild.get_member(int(overwrite_id))

                if overwrite is None:
                    failures.append(
                        f"Overwrite ID `{overwrite_id}` did not resolve to a role or member in this guild"
                    )
                    continue

                try:
                    await category.set_permissions(overwrite, **permissions)
                except Exception as ex:
                    failures.append(
                        f"Could not update permissions for category ID {json_category_id} and overwrite ID {overwrite_id}"
                    )
                    _log.warning(
                        "Could not update permissions for category ID %s and overwrite ID %s",
                        json_category_id,
                        overwrite_id,
                        exc_info=ex,
                    )
                    break

    async def import_permissions_json_channels(
        self, ctx: commands.Context, json_guild: JsonGuild, failures: list[str]
    ):
        for json_channel_id, json_channel in json_guild["channels"].items():
            channel = ctx.guild.get_channel(int(json_channel_id))

            if channel is None:
                failures.append(
                    f"ID `{json_channel_id}` did not resolve to a channel in this guild"
                )
                continue

            if isinstance(channel, discord.CategoryChannel):
                failures.append(f"ID `{json_channel_id}` is a category channel")
                continue

            if json_channel["synced"] and not channel.permissions_synced:
                try:
                    await channel.edit(sync_permissions=True)
                except Exception as ex:
                    failures.append(
                        f"Could not sync permissions for channel ID {json_channel_id}"
                    )
                    _log.warning(
                        "Could not sync permissions for channel ID %s",
                        json_channel_id,
                        exc_info=ex,
                    )
                finally:
                    continue

            for overwrite_id, permissions in json_channel["overwrites"].items():
                if not permissions:
                    continue

                overwrite = ctx.guild.get_role(
                    int(overwrite_id)
                ) or ctx.guild.get_member(int(overwrite_id))

                if overwrite is None:
                    failures.push(
                        f"Overwrite ID `{overwrite_id}` did not resolve to a role or member in this guild"
                    )
                    continue

                try:
                    await channel.set_permissions(overwrite, **permissions)
                except Exception as ex:
                    failures.append(
                        f"Could not update permissions for channel ID {json_channel_id} and overwrite ID {overwrite_id}"
                    )
                    _log.warning(
                        "Could not update permissions for channel ID %s and overwrite ID %s",
                        json_channel_id,
                        overwrite_id,
                        exc_info=ex,
                    )
                    break

    @permissions.command(name="export")
    async def permissions_export(self, ctx: commands.Context):
        """Export a permissions object from the current guild."""

        async with ctx.typing():
            try:
                json_file = self.export_permissions_json(ctx.guild)
                await ibis.reply.success(ctx, file=json_file)
            except Exception as ex:
                await ibis.reply.fail(
                    ctx, "Building permissions JSON failed, please see log."
                )
                raise ex

    def export_permissions_json(self, guild: discord.Guild):
        fp = StringIO()

        obj = {
            "id": guild.id,
            "name": guild.name,
            "roles": {
                role.id: {
                    "name": role.name,
                    "permissions": dict(role.permissions),
                }
                for role in guild.roles
            },
            "members": {
                member.id: {
                    "username": member.name,
                    "roles": [role.id for role in member.roles],
                }
                for member in guild.members
            },
            "categories": {
                category.id: {
                    "name": category.name,
                    "overwrites": {
                        overwrites.id: {
                            permission: value
                            for (permission, value) in category.overwrites_for(
                                overwrites
                            )
                            if value is not None
                        }
                        for overwrites in category.overwrites
                    },
                }
                for category in guild.categories
            },
            "channels": {
                channel.id: {
                    "name": channel.name,
                    "category": channel.category_id,
                    "overwrites": {
                        overwrites.id: {
                            permission: value
                            for (permission, value) in channel.overwrites_for(
                                overwrites
                            )
                            if value is not None
                        }
                        for overwrites in channel.overwrites
                    },
                    "synced": channel.permissions_synced,
                }
                for channel in guild.channels
                if not isinstance(channel, discord.CategoryChannel)
            },
        }

        json.dump(obj, fp, indent=2)

        fp.seek(0)
        return discord.File(fp=fp, filename=ibis.file.unique("permissions.json"))
