from io import StringIO

from redbot.core import commands, Config
import discord

from datetime import datetime
import csv


class CsvMembers(commands.Cog):
    def __init__(self):
        self.config = Config.get_conf(
            self, identifier=778440330267960653, force_registration=True
        )

    @commands.command()
    @commands.admin()
    async def csvmembers(self, ctx: commands.Context):
        "Generate a CSV of all members in the server"

        csv_file = self.build_csv(ctx.guild)
        await ctx.reply(file=csv_file)

    def build_csv(self, guild: discord.Guild) -> discord.File:
        date = datetime.now().strftime("%Y%m%d%H%M%S")
        fp = StringIO()
        writer = csv.writer(fp)
        writer.writerow(
            [
                "Username",
                "Guild Display Name",
                "Display Name (If Different)",
            ]
        )
        print(guild.members)
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
                ]
            )

        fp.seek(0)
        return discord.File(fp=fp, filename=f"{date}.members.csv")
