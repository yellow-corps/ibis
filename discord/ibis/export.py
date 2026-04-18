from io import BytesIO
from zoneinfo import ZoneInfo
from aiohttp import ClientSession
from redbot.core import Config
import discord

__internal_config: Config = None


class ExportException(Exception):
    pass


def config() -> Config:
    global __internal_config
    if not __internal_config:
        __internal_config = Config.get_conf(
            cog_instance=None,
            cog_name="TimeZone",
            identifier=863117321820307876,
            force_registration=True,
        )
        default_global = {"timezone": None}
        __internal_config.register_global(**default_global)

    return __internal_config


async def channel(target: discord.TextChannel, file_format: str) -> discord.File:
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
