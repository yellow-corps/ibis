from abc import ABC, abstractmethod
from collections.abc import Callable
from io import StringIO
from typing import Union
from redbot.core import commands, Config
from redbot.core.utils import predicates
import discord
from discord.ext import tasks
import ibis


class InviteHandler(ABC):
    def __init__(
        self,
        ctx: commands.Context,
        finish_callback: Callable,
    ):
        self.ctx = ctx
        self.finish_callback = finish_callback

    @abstractmethod
    async def flush(self):
        pass

    @abstractmethod
    def should_stop(self):
        pass

    @abstractmethod
    async def loop(self):
        pass

    async def start(self):
        await self.ctx.react_quietly("⏳")
        await self.process.start()

    async def stop(self, successful: bool = False):
        self.process.stop()
        await self.ctx.message.remove_reaction("⏳", self.ctx.me)
        if successful:
            await ibis.reply.success(self.ctx.message)
        await self.flush()
        self.finish_callback()

    @tasks.loop(seconds=1.0)
    async def process(self):
        if self.should_stop():
            return await self.stop(True)

        try:
            async with self.ctx.typing():
                await self.loop()
        except Exception as ex:
            await ibis.reply.fail(
                self.ctx.message, "An error occurred while processing invites."
            )
            await self.stop()
            raise ex


class InviteCreator(InviteHandler):
    def __init__(
        self,
        ctx: commands.Context,
        channel: Union[discord.TextChannel, discord.ForumChannel],
        amount: int,
        finish_callback: Callable,
    ):
        super().__init__(ctx, finish_callback)
        self.channel = channel
        self.invites = []
        self.amount = amount

    async def flush(self):
        file = discord.File(
            fp=StringIO("\n".join(self.invites)), filename="invites.txt"
        )
        await self.ctx.reply(
            f"{len(self.invites)}/{self.amount} invites created for {self.channel.mention}",
            file=file,
        )

    def should_stop(self):
        return len(self.invites) >= self.amount

    async def loop(self):
        self.invites.append(
            (
                await self.channel.create_invite(
                    reason="auto invite creation", max_age=0, max_uses=1, unique=True
                )
            ).url
        )


class InviteRevoker(InviteHandler):
    def __init__(
        self,
        ctx: commands.Context,
        channel: Union[discord.TextChannel, discord.ForumChannel],
        invites: list[discord.Invite],
        finish_callback: Callable,
    ):
        super().__init__(ctx, finish_callback)
        self.channel = channel
        self.invites = invites
        self.amount = len(invites)

    async def flush(self):
        processed = self.amount - len(self.invites)
        await self.ctx.reply(
            f"{processed}/{self.amount} invites revoked for {self.channel.mention}"
        )

    def should_stop(self):
        return len(self.invites) == 0

    async def loop(self):
        await self.invites.pop().delete(reason="auto invite revocation")


class UniqueInvites(commands.Cog):
    def __init__(self):
        self.config = Config.get_conf(
            self, identifier=278581805461420503, force_registration=True
        )

        self.handler = None

    @commands.group()
    @commands.admin()
    async def uniqueinvites(self, ctx: commands.Context):
        "UniqueInvites commands"

    @uniqueinvites.command()
    async def create(
        self,
        ctx: commands.Context,
        channel: Union[discord.TextChannel, discord.ForumChannel],
        amount: int = 1,
    ):
        """Create unique, non-expiring, single use invites for the specified channel"""

        if amount <= 0:
            await ibis.reply.fail(
                ctx.message, "Must specify a positive amount of invites to create"
            )

        if amount > 1000:
            await ibis.reply.fail(
                ctx.message,
                "For everyone's sanity, you must specify an amount of invites less than or equal "
                + "to 1000",
            )

        if not self.handler:
            self.handler = InviteCreator(ctx, channel, amount, self.finish_callback)
            await self.handler.start()
        else:
            await ibis.reply.fail(
                ctx.message, "Already in the process of handling invites, please wait."
            )

    @uniqueinvites.command()
    async def revoke(
        self,
        ctx: commands.Context,
        channel: Union[discord.TextChannel, discord.ForumChannel],
    ):
        """Revoke all unique, non-expiring, single use invites for the specified channel"""
        invites = list(
            filter(
                lambda invite: (invite.expires_at is None) and (invite.max_uses == 1),
                await channel.invites(),
            )
        )

        if len(invites) == 0:
            return await ibis.reply.fail(
                ctx.message, f"No invites to revoke for {channel.mention}"
            )

        await ctx.reply(f"Revoke {len(invites)} invites from {channel.mention}?")
        pred = predicates.MessagePredicate.yes_or_no(ctx)
        await ctx.bot.wait_for("message", check=pred)
        if not pred.result:
            return

        if not self.handler:
            self.handler = InviteRevoker(ctx, channel, invites, self.finish_callback)
            await self.handler.start()
        else:
            await ibis.reply.fail(
                ctx.message, "Already in the process of handling invites, please wait."
            )

    @uniqueinvites.command(name="stop")
    async def stop(self, ctx: commands.Context):
        """Stops an ongoing invite process and outputs the current invites generated"""
        if self.handler:
            await self.handler.stop()
            await ibis.reply.success(ctx.message, "Stopped process")
        else:
            await ibis.reply.fail(ctx.message, "Not running an invite process")

    def finish_callback(self):
        self.handler = None
