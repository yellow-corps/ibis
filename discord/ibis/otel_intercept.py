import os
import logging

otel_enabled = bool(os.getenv("WITH_OTEL"))
if otel_enabled:
    from opentelemetry import trace

    tracer = trace.get_tracer("red.cogs.ibis.otel")
else:
    tracer = {}

logger = logging.getLogger("red.cogs.ibis.otel")


async def invoke_intercept(ctx, invoke):
    with tracer.start_as_current_span(
        f"[@] {ctx.command.name}" if ctx.command else "[@] <unknown command invoked>"
    ) as span:
        if ctx.message:
            span.set_attributes(
                {
                    "discord.message.id": ctx.message.id,
                    "discord.message.content": ctx.message.content,
                }
            )

        if ctx.author:
            span.set_attributes(
                {
                    "discord.user.id": ctx.author.id,
                    "discord.user.name": ctx.author.name,
                }
            )

        if ctx.channel:
            span.set_attribute("discord.channel.id", ctx.channel.id)
            if hasattr(ctx.channel, "name"):
                span.set_attribute("discord.channel.name", ctx.channel.name)

        if ctx.guild:
            span.set_attributes(
                {"discord.guild.id": ctx.guild.id, "discord.guild.name": ctx.guild.name}
            )

        if ctx.command:
            span.set_attribute("discord.command.name", ctx.command.name)

        logger.info("hello world")

        await invoke(ctx)
