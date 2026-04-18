import functools
import os
import inspect

otel_enabled = bool(os.getenv("WITH_OTEL"))
if otel_enabled:
    from opentelemetry import trace
    from opentelemetry.trace.span import Span

    tracer = trace.get_tracer("red.cogs.ibis.otel")
else:
    Span = any
    tracer: any = {}


def start_span(func, name: str = None):
    """
    Decorator to start a new span on a given function or method
    """

    if not otel_enabled:
        return func

    def configure_span(span: Span):
        span.set_attribute("function.name", func.__name__)
        span.set_attribute("function.module", inspect.getmodule(func).__name__)

    if inspect.iscoroutinefunction(func):
        if inspect.ismethod(func):

            @functools.wraps(func)
            async def async_method_wrapper(self, *args, **kwargs):
                with tracer.start_as_current_span(
                    name if name else func.__name__
                ) as span:
                    configure_span(span)
                    return await func(self, *args, **kwargs)

            return async_method_wrapper

        @functools.wraps(func)
        async def async_func_wrapper(*args, **kwargs):
            with tracer.start_as_current_span(name if name else func.__name__) as span:
                configure_span(span)
                return await func(*args, **kwargs)

        return async_func_wrapper

    if inspect.ismethod(func):

        @functools.wraps(func)
        def sync_method_wrapper(self, *args, **kwargs):
            with tracer.start_as_current_span(name if name else func.__name__) as span:
                configure_span(span)
                return func(self, *args, **kwargs)

        return sync_method_wrapper

    @functools.wraps(func)
    def sync_func_wrapper(*args, **kwargs):
        with tracer.start_as_current_span(name if name else func.__name__) as span:
            configure_span(span)
            return func(*args, **kwargs)

    return sync_func_wrapper


def add_span_attribute(key: str, value: any = "", span: Span = None):
    """Add an attribute to the given span, or the current span if none is provided"""
    if otel_enabled:
        if not span:
            span = trace.get_current_span()
        span.set_attribute(f"discord.{key}", value)
