from zoneinfo import ZoneInfo
from redbot.core import commands
import ibis


class TimeZoneCog(commands.Cog):
    def __init__(self):
        self.config = ibis.export.config()

    async def get_timezone(self) -> ZoneInfo:
        try:
            return ZoneInfo(await self.config.timezone())
        except:
            return None

    async def set_timezone(self, timezone: ZoneInfo):
        await self.config.timezone.set(timezone.key)

    @commands.command()
    @commands.is_owner()
    async def timezone(self, ctx: commands.Context, timezone: ZoneInfo):
        "Get or set the timezone to use"

        if not timezone:
            return await ibis.reply.success(
                ctx.message, f"Timezone: {(await self.get_timezone())}"
            )
        else:
            await self.set_timezone(timezone)
            await ibis.reply.success(ctx.message)
