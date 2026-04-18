from typing import Union, Optional
from zoneinfo import ZoneInfo
from redbot.core import commands
import ibis


class TimeZoneCog(commands.Cog):
    def __init__(self):
        self.config = ibis.export.config()

    async def get_timezone(self) -> Union[ZoneInfo, None]:
        try:
            return ZoneInfo(await self.config.timezone())
        except Exception:
            return None

    async def set_timezone(self, timezone: ZoneInfo):
        await self.config.timezone.set(timezone.key)

    @commands.command()
    @commands.is_owner()
    async def timezone(self, ctx: commands.Context, timezone: Optional[ZoneInfo]):
        "Get or set the timezone to use"

        if not timezone:
            await ibis.reply.success(
                ctx.message, f"Timezone: {(await self.get_timezone())}"
            )
            return

        await self.set_timezone(timezone)
        await ibis.reply.success(ctx.message)
