from io import BytesIO
from aiohttp import ClientSession
from redbot.core import commands, Config
from zoneinfo import ZoneInfo
import discord


__internal_config: Config = None


def config():
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


async def channel(
    channel: discord.TextChannel,
    file_format: str,
    *,
    bot: commands.Bot = None,
) -> discord.File:
    file_ext = "zip" if file_format == "html" else "txt"

    params = {}
    headers = {}

    if bot:
        params["botName"] = bot.user.name

    try:
        timezone_str = await config().timezone()
        if timezone_str:
            headers["tz"] = ZoneInfo(timezone_str).key
    except:
        pass

    async with ClientSession("http://localhost:8081") as session:
        async with session.get(
            f"/channel/{channel.id}/{file_ext}", headers=headers, params=params
        ) as response:
            if response.status != 200:
                raise ExportException(
                    f"Attempted to export channel, but got a {response.status} HTTP status."
                )
            return discord.File(
                fp=BytesIO(await response.read()),
                filename=f"{channel.name}.{file_format}.{file_ext}",
            )
