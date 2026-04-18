from io import BytesIO
from zoneinfo import ZoneInfo
from aiohttp import ClientSession
from redbot.core import Config
import discord
from ibis.otel import start_span, add_span_attribute

__INTERNAL_CONFIG: Config = None


class ExportException(Exception):
    pass


def config():
    # pylint: disable-next=global-statement
    global __INTERNAL_CONFIG
    if not __INTERNAL_CONFIG:
        __INTERNAL_CONFIG = Config.get_conf(
            cog_instance=None,
            cog_name="TimeZone",
            identifier=863117321820307876,
            force_registration=True,
        )
        default_global = {"timezone": None}
        __INTERNAL_CONFIG.register_global(**default_global)

    return __INTERNAL_CONFIG


@start_span
async def channel(target: discord.TextChannel, file_format: str) -> discord.File:
    add_span_attribute("export.channel.id", target.id)
    add_span_attribute("export.channel.id", target.name)
    add_span_attribute("export.file_format", file_format)
    file_ext = "zip" if file_format == "html" else "txt"

    headers = {}

    try:
        timezone_str = await config().timezone()
        if timezone_str:
            headers["tz"] = ZoneInfo(timezone_str).key
    except Exception:
        # if failed to get timezone, just continue
        pass

    async with ClientSession("http://localhost:8081") as session:
        async with session.get(
            f"/channel/{target.id}/{file_ext}", headers=headers
        ) as response:
            if response.status != 200:
                raise ExportException(
                    f"Attempted to export channel, but got a {response.status} HTTP status."
                )
            return discord.File(
                fp=BytesIO(await response.read()),
                filename=f"{target.name}.{file_format}.{file_ext}",
            )
