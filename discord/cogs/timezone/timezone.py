from typing import Union, Optional
from zoneinfo import ZoneInfo
from redbot.core import commands, Config
import ibis


class TimeZoneCog(commands.Cog):
    def __init__(self, config: Config):
        self.config = config

    async def get_timezone(self) -> Union[ZoneInfo, None]:
        try:
            return ZoneInfo(await self.config.timezone())
        # pylint: disable-next=broad-exception-caught
        except Exception:
            return None

    async def set_timezone(self, timezone: Optional[ZoneInfo]):
        await self.config.timezone.set(timezone.key if timezone else None)

    @commands.group()
    @commands.is_owner()
    async def timezone(self, ctx: commands.Context):
        "Timezone"

    @timezone.command()
    @commands.is_owner()
    async def timezone_get(self, ctx: commands.Context):
        "Get the timezone"
        await ibis.reply.success(ctx, f"Timezone: {(await self.get_timezone())}")

    @timezone.command()
    @commands.is_owner()
    async def timezone_set(self, ctx: commands.Context, timezone: ZoneInfo):
        "Set the timezone"

        await self.set_timezone(timezone)
        await ibis.reply.success(ctx)

    @timezone.command()
    @commands.is_owner()
    async def timezone_clear(self, ctx: commands.Context):
        "Clear the timezone"

        await self.set_timezone(None)
        await ibis.reply.success(ctx)
