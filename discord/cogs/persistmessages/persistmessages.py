import asyncio
import json
import logging
from redbot.core import commands, Config, data_manager
import duckdb
import discord
import ibis

_log = logging.getLogger(__name__)


class PersistMessages(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # yeah, look, this is suuuuuuuuper dodgy, but I still wanna do it okay?
        # pylint: disable-next=protected-access
        self.state = bot._connection

        self.config = Config.get_conf(
            self, identifier=931967579004876408, force_registration=True
        )

        default_global = {
            "enabled": False,
        }

        self.config.register_global(**default_global)

        cog_data_path = data_manager.cog_data_path(self)
        db_path = f"{cog_data_path}/messages.db"
        self.db = duckdb.connect(db_path)
        self.db.sql(
            """
            CREATE TABLE IF NOT EXISTS messages (
              id BIGINT PRIMARY KEY,
              data JSON
            );
            """
        )

        self.enabled = False
        self.init_enabled()

        self.orig_parse_message_create = self.state.parsers["MESSAGE_CREATE"]
        self.state.parsers["MESSAGE_CREATE"] = self.parse_message_create
        self.orig_parse_message_update = self.state.parsers["MESSAGE_UPDATE"]
        self.state.parsers["MESSAGE_UPDATE"] = self.parse_message_update
        # pylint: disable-next=protected-access
        self.orig_get_message = self.state._get_message
        # pylint: disable-next=protected-access
        self.state._get_message = self.get_message

    def init_enabled(self):
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():

            def set_self_enabled(task: asyncio.Task[bool]):
                self.enabled = task.result()

            task = loop.create_task(self.get_enabled())
            task.add_done_callback(set_self_enabled)
        else:
            self.enabled = asyncio.run(self.get_enabled())

    async def get_enabled(self) -> bool:
        return await self.config.enabled()

    async def set_enabled(self, enabled: bool):
        self.enabled = enabled
        await self.config.enabled.set(enabled)

    @commands.group()
    @commands.is_owner()
    async def persistmessages(self, ctx: commands.Context):
        """PersistMessages commands"""

    @persistmessages.command(name="set")
    async def persistmessages_enable(self, ctx: commands.Context, enabled: bool = None):
        """Enable or disable the PersistMessages cog to actually monitor"""
        if enabled is None:
            enabled = "enabled" if await self.get_enabled() else "disabled"
            await ibis.reply.success(
                ctx.message, f"PersistMessages is currently {enabled}"
            )
        else:
            await self.set_enabled(enabled)
            await ibis.reply.success(ctx.message)

    def store_message(self, data: discord.Message):
        try:
            self.db.execute(
                "INSERT OR REPLACE INTO messages VALUES (?, ?)", [int(data["id"]), data]
            )
        except Exception as ex:
            _log.warning(
                "Swallowed an exception while saving a persisted message", exc_info=ex
            )

    def fetch_message(self, msg_id: int) -> discord.Message | None:
        try:
            results = self.db.execute(
                "SELECT data FROM messages WHERE id = ? LIMIT 1", [msg_id]
            ).fetchone()

            if not results:
                return None

            data = json.loads(results[0])
            channel = self.bot.get_channel(int(data["channel_id"]))
            persisted_message = discord.Message(
                state=self.state, channel=channel, data=data
            )
            # pylint: disable-next=protected-access
            self.state._messages.append(persisted_message)
            return persisted_message
        except Exception as ex:
            _log.warning(
                "Swallowed an exception while loading a persisted message", exc_info=ex
            )
        return None

    def parse_message_create(self, data: discord.Message):
        self.orig_parse_message_create(data)
        if self.enabled:
            self.store_message(data)

    def parse_message_update(self, data: discord.Message):
        self.orig_parse_message_update(data)
        if self.enabled:
            self.store_message(data)

    def get_message(self, msg_id: int | None) -> discord.Message | None:
        cached_message = self.orig_get_message(msg_id)
        if cached_message:
            return cached_message
        if self.enabled:
            return self.fetch_message(msg_id)
        return None
