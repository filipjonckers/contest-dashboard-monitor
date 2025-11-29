import configparser
import logging
import os
from typing import Any

CONFIG_FILE = 'contest_scoreboard_monitor.ini'
config: configparser.ConfigParser = configparser.ConfigParser()


def load_user_config() -> None:
    """Load configuration from the ini file."""
    if os.path.exists(CONFIG_FILE):
        config.read(CONFIG_FILE)
        logging.debug(f'Configuration loaded from {CONFIG_FILE}')
    else:
        logging.warning(f'Configuration file {CONFIG_FILE} not found. Using defaults.')


def get_config_value(section: str, option: str, default: Any = None) -> Any:
    """Get a configuration value with a default fallback."""
    try:
        return config.get(section, option)
    except (configparser.NoSectionError, configparser.NoOptionError):
        logging.warning(f'Config option [{section}] {option} not found. Using default: {default}')
        return default


def set_config_value(section: str, option: str, value: Any) -> None:
    """Set a configuration value and save to the ini file."""
    if not config.has_section(section):
        config.add_section(section)
    config.set(section, option, str(value))
    with open(CONFIG_FILE, 'w') as configfile:
        config.write(configfile)
    logging.debug(f'Config option [{section}] {option} set to {value} and saved to {CONFIG_FILE}')
