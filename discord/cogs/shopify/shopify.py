from datetime import datetime
from typing import Union, Literal
import re
from redbot.core import commands, Config
import discord


class ShopifyOrder:
    def __init__(self, bot: commands.Bot, body):
        self._bot = bot
        self._name = str(body["name"])
        self._shop = str(body["shop"])
        self._url = str(body["order_status_url"])
        self._created_at = str(body["created_at"])
        self._updated_at = str(body["updated_at"])
        self._other_events = ShopifyUtils.find_events(body)
        self._customer = ShopifyUtils.find_customer(body["customer"])
        self._products = ShopifyUtils.find_products(body["line_items"])

    def order_name(self) -> str:
        return f"Order {self._name}"

    def url(self) -> str:
        return self._url

    def shop(self) -> str:
        return self._shop

    def created_at(self) -> str:
        return ShopifyUtils.format_timestamp(self._created_at)

    def customer(self) -> Union[discord.User, None]:
        # try to match exactly first
        customer = discord.utils.find(
            lambda u: u.name in self._customer,
            self._bot.users,
        )

        if customer:
            return customer

        # otherwise, sanitise before matching
        return discord.utils.find(
            lambda u: ShopifyUtils.sanitise_name(u.name)
            in [ShopifyUtils.sanitise_name(name) for name in self._customer],
            self._bot.users,
        )

    def mention_customer(self) -> str:
        user = self.customer()
        if user:
            return user.mention
        return " ".join(self._customer)

    def products(self) -> str:
        return "\n".join(
            [
                f"`{str(product['quantity']).rjust(3)}x` {product['name']}"
                for product in self._products
            ]
        )

    def is_actually_update(self) -> bool:
        if not (self._updated_at or self._other_events):
            return False

        updated_at = datetime.fromisoformat(self._updated_at)

        for event in self._other_events:
            if abs(event - updated_at).seconds < 5:
                return False

        return True


class ShopifyUtils:

    @staticmethod
    def find_events(body) -> list[datetime]:
        return [
            datetime.fromisoformat(event)
            for event in [body["created_at"], body["closed_at"], body["cancelled_at"]]
            + [
                fulfillment["created_at"]
                for fulfillment in body.get("fulfillments", [])
            ]
            if event is not None
        ]

    @staticmethod
    def sanitise_name(name: str) -> str:
        return re.sub(r"[._ ]", "", name.lower())

    @staticmethod
    def find_customer(customer) -> list[str]:
        customer = (
            customer
            if customer
            else {"first_name": "<unknown customer>", "last_name": ""}
        )

        return [
            str(customer["first_name"]),
            str(customer["last_name"]),
        ]

    @staticmethod
    def find_products(line_items) -> list:
        return [
            {"name": str(line_item["name"]), "quantity": int(line_item["quantity"])}
            for line_item in line_items
        ]

    @staticmethod
    def format_timestamp(iso_timestamp: str) -> str:
        timestamp = datetime.fromisoformat(iso_timestamp)

        short_timestamp = discord.utils.format_dt(timestamp, "f")
        relative_timestamp = discord.utils.format_dt(timestamp, "R")
        return f"{short_timestamp}, {relative_timestamp}"

    @staticmethod
    def build_embed(event: str, order: ShopifyOrder):
        embed = discord.Embed(
            title=f"{order.order_name()} {event}",
            description=order.products(),
            url=order.url(),
        )
        embed.add_field(name="Placed By", value=order.mention_customer())
        embed.add_field(name="Placed At", value=order.created_at())
        embed.set_footer(text=order.shop())
        return embed


class Shopify(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

        self.config = Config.get_conf(
            self, identifier=410722909754055635, force_registration=True
        )

        default_global = {
            "shop_channel": False,
            "messages": {
                "created": "{} was created.",
                "updated": "{} was updated.",
                "fulfilled": "{} was fulfilled.",
                "cancelled": "{} was cancelled.",
            },
            "staff": [],
        }

        self.config.register_global(**default_global)

    async def get_channel(self) -> Union[discord.TextChannel, discord.ForumChannel]:
        return self.bot.get_channel(await self.config.shop_channel())

    async def set_channel(
        self, channel: Union[discord.TextChannel, discord.ForumChannel], /
    ):
        await self.config.shop_channel.set(channel.id)

    async def get_message(self, message_type: str, name: str = None, /) -> str:
        message = (await self.config.messages())[message_type]
        if name:
            return message.format(name)
        return message

    async def set_message(self, message_type: str, message: str, /):
        messages = await self.config.messages()
        messages[message_type] = message
        await self.config.messages.set(messages)

    async def get_staff(self) -> list[Union[discord.User, discord.Role]]:
        return [
            self.bot.get_member(id) or self.bot.get_role(id)
            for id in await self.config.staff()
        ]

    async def set_staff(self, users: list[Union[discord.User, discord.Role]]):
        await self.config.staff.set([u.id for u in users])

    async def reply_success(self, message: discord.Message, reply: str = None):
        if reply:
            await message.reply(reply)
        await message.add_reaction("✅")

    async def reply_fail(self, message: discord.Message, reply: str):
        await message.reply(reply)
        await message.add_reaction("❌")

    @commands.group()
    @commands.is_owner()
    async def shopify(self, ctx: commands.Context):
        """Shopify commands"""

    @shopify.command(name="channel")
    async def shopify_channel(
        self,
        ctx: commands.Context,
        channel: Union[discord.TextChannel, discord.ForumChannel, None],
    ):
        """Globally get or set Shopify output channel."""
        if not channel:
            await self.reply_success(
                ctx.message,
                f"Shopify channel currently set to {(await self.get_channel()).mention}",
            )
        else:
            await self.set_channel(channel)
            await self.reply_success(ctx.message)

    @shopify.command(name="message")
    async def shopify_message(
        self,
        ctx: commands.Context,
        message_type: Literal["created", "updated", "fulfilled", "cancelled"],
        *,
        content: str = None,
    ):
        """Globally get or set Shopify messages for events."""
        if not content:
            content = await self.get_message(message_type)
            await self.reply_success(
                ctx.message,
                f"Current message for `{message_type}` events is `{content}`.",
            )
        else:
            await self.set_message(message_type, content)
            await self.reply_success(ctx.message)

    @shopify.group(name="staff", autohelp=False)
    async def shopify_staff(self, ctx: commands.Context):
        """Globally add or remove staff for being added to order threads."""
        if not ctx.invoked_subcommand:
            users = ", ".join(u.mention for u in await self.get_staff())
            if users:
                await self.reply_success(ctx.message, f"Current staff: {users}")
            else:
                await self.reply_success(ctx.message, "No staff currently added.")

    @shopify_staff.command(name="add")
    async def shopify_staff_add(
        self,
        ctx: commands.Context,
        users: commands.Greedy[Union[discord.User, discord.Role]],
    ):
        """Globally add staff to being added to order threads."""
        if not users:
            return await self.reply_fail(
                ctx.message,
                "No users provided or I cannot see any of the users you mentioned.",
            )

        current_staff = await self.config.staff()
        new_staff = list(set(current_staff + users))

        if current_staff == new_staff:
            return await self.reply_fail(
                ctx.message, "All of the users provided were already marked as staff."
            )

        await self.config.staff.set(new_staff)
        await self.reply_success(ctx.message)

    @shopify_staff.command(name="remove")
    async def shopify_staff_remove(
        self,
        ctx: commands.Context,
        users: commands.Greedy[Union[discord.User, discord.Role]],
    ):
        """Globally remove staff from being added to order threads."""
        if not users:
            return await self.reply_fail(
                ctx.message,
                "No users provided or I cannot see any of the users you mentioned.",
            )

        current_staff = await self.config.staff()
        new_staff = list(set(current_staff) - set(users))

        if current_staff == new_staff:
            return await self.reply_fail(
                ctx.message, "None of the users provided were marked as staff."
            )

        await self.config.staff.set(new_staff)
        await self.reply_success(ctx.message)

    async def webhook(self, topic: str, body) -> bool:
        if not await self.config.shop_channel():
            return True

        order = ShopifyOrder(self.bot, body)

        match topic:
            case "ORDERS_CREATE":
                await self.orders_created(order)
            case "ORDERS_UPDATED":
                await self.orders_updated(order)
            case "ORDERS_FULFILLED":
                await self.orders_fulfilled(order)
            case "ORDERS_CANCELLED":
                await self.orders_cancelled(order)

        return True

    async def orders_created(self, order: ShopifyOrder):
        thread = await self.find_or_open_thread("created", order)
        await thread.send(await self.get_message("created", order.order_name()))

    async def orders_updated(self, order: ShopifyOrder):
        if not order.is_actually_update():
            return

        thread = await self.find_or_open_thread("updated", order, emit_embed=True)
        await thread.send(await self.get_message("updated", order.order_name()))

    async def orders_fulfilled(self, order: ShopifyOrder):
        thread = await self.find_or_open_thread("fulfilled", order)
        await thread.send(await self.get_message("fulfilled", order.order_name()))

    async def orders_cancelled(self, order: ShopifyOrder):
        thread = await self.find_or_open_thread("cancelled", order)
        await thread.send(await self.get_message("cancelled", order.order_name()))

    async def find_or_open_thread(
        self, event: str, order: ShopifyOrder, *, emit_embed: bool = False
    ) -> discord.Thread:
        channel = await self.get_channel()

        thread = discord.utils.find(
            lambda t: t.name == order.order_name(), channel.threads
        )

        if not thread:
            emit_embed = True

            thread = await channel.create_thread(
                name=order.order_name(), type=discord.ChannelType.public_thread
            )

            customer = order.customer()
            if customer:
                await thread.add_user(customer)

            for user in await self.get_staff():
                await thread.add_user(user)

        if emit_embed:
            await thread.send(embed=ShopifyUtils.build_embed(event, order))

        return thread
