from io import StringIO
import csv
from redbot.core import commands, Config
import discord
import ibis


# pylint: disable-next=too-few-public-methods
class CsvMembersBuilder:
    def build_csv(self, guild: discord.Guild) -> discord.File:
        fp = StringIO()
        writer = csv.writer(fp)
        writer.writerow(
            ["Username", "Guild Display Name", "Display Name (If Different)", "Roles"]
        )
        for member in guild.members:
            writer.writerow(
                [
                    member.name,
                    member.display_name,
                    (
                        member.global_name
                        if not member.display_name == member.global_name
                        else ""
                    ),
                    " ".join(
                        f"@{role.name}"
                        for role in member.roles
                        if role.name != "@everyone"
                    ),
                ]
            )

        fp.seek(0)
        return discord.File(fp=fp, filename=ibis.file.unique("members.csv"))


class CsvMembersCog(commands.Cog):
    def __init__(self, builder_cls=CsvMembersBuilder):
        self.config = Config.get_conf(
            self, identifier=778440330267960653, force_registration=True
        )
        self.builder = builder_cls()

    @commands.command()
    @commands.admin()
    async def csvmembers(self, ctx: commands.Context):
        "Generate a CSV of all members in the server"

        print(ctx)

        async with ctx.typing():
            try:
                csv_file = self.builder.build_csv(ctx.guild)
                await ibis.reply.success(ctx, file=csv_file)
            except Exception as ex:
                await ibis.reply.fail(
                    ctx, "Building member CSV failed, please see log."
                )
                raise ex
