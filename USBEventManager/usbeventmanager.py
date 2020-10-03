import click
import logging

from core import USBEventManager

logger = logging.getLogger(__name__)


class Config(object):
    def __init__(self):
        self.loglevel = (False,)
        self.no_actions = False


pass_config = click.make_pass_decorator(Config, ensure=True)


@click.group()
@click.option(
    "--loglevel",
    default="INFO",
    type=click.Choice(["ERROR", "WARNING", "INFO", "DEBUG"]),
    help="Sets the logging level. Defaults to WARNING.",
)
@click.option(
    "--no-actions",
    required=False,
    is_flag=True,
    default=False,
    help="Don't actually perform any actions. Used for testing and development.",
)
@pass_config
def cli(config, loglevel, no_actions):
    config.loglevel = loglevel
    config.no_actions = no_actions

    # Logging
    numeric_logging_level = getattr(logging, config.loglevel, None)
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_logging_level)
    formatter = logging.Formatter("%(message)s")
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    root_logger.addHandler(console)

    config.uev = USBEventManager(no_actions=no_actions)


@cli.command(help="Monitor for added and removed USB devices")
@pass_config
def monitor(config):
    """ Monitor for added and removed USB devices """
    uev = config.uev
    uev.monitor()


@cli.command(
    help="Remove one or more USB devices from the configuration. -> "
    '\'remove "xxxx:xxxx" "yyyy:yyyy"\''
)
@click.argument("device_ids", required=True, nargs=-1, type=str)
@pass_config
def remove(config, device_ids: tuple):
    """ Removes USB devices from the config """
    uev = config.uev
    uev.remove_devices(device_ids=device_ids)


@cli.command(help="List enabled actions.")
@pass_config
def list_actions(config):
    """ Outputs a list of devices in the config file """
    uev = config.uev
    uev.list_actions()


@pass_config
@cli.command(help="List devices in the config file.")
@pass_config
def list_devices(config):
    """ Outputs a list of devices in the config file """
    uev = config.uev
    uev.list_devices()


@cli.command(help="Learn new USB devices.")
@pass_config
def learn(config):
    uev = config.uev
    uev.learn()


@cli.command(help="Configure USBEventManager to start automatically.")
@pass_config
def automatic_start(config):
    """ Create a service """
    uev = config.uev
    uev.create_service()


if __name__ == "__main__":
    cli()
