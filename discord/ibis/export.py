from redbot.core import Config


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
