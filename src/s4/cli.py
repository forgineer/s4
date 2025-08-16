import click
import json
import os
import secrets
import sqlite3

from s4.server import app
from s4 import __version__


def generate_secret_key() -> str:
    """
    Generates a random secret key for Flask and s4 DB access.

    :return: A securely generated secret key.
    """
    return secrets.token_urlsafe(32)


def generate_config_file(config_file_path: str, database_file_path: str) -> dict:
    """
    Generates a configuration file for s4 with a random secret key and database file path.
    
    :param config_file_path: The path where the configuration file will be saved.
    :param database_file_path: The path to the SQLite database file.
    :return: A dictionary containing the configuration settings.
    """
    _config: dict = {
        'SECRET_KEY': generate_secret_key(),
        'DATABASE': database_file_path
    }

    with open(config_file_path, "w") as file:
        json.dump(_config, file, indent=4)
    
    return _config


def configure_s4() -> None:
    """
    Creates a config and database file with a generated SECRET_KEY value for Flask.

    :return: None
    """
    # Define the current working directory, config file, database file, and path
    config_file_name: str = 'config.json'
    database_file_name: str = 's4.db'
    config: dict = {}

    # Create the Flask app instance
    instance_path = app.instance_path
    if not os.path.exists(instance_path):
        os.makedirs(instance_path)
    
    # Define the full paths for the config and database files
    config_file_path = os.path.join(instance_path, config_file_name)
    database_file_path = os.path.join(instance_path, database_file_name)

    # Define s4 database file and secret key
    try:
        sqlite3.connect(database_file_path)
    except sqlite3.Error as e:
        click.echo(f'An error occurred while establishing the s4 database: {e}')
        return

    if os.path.exists(config_file_path):
        if click.confirm('The configuration file already exists. Do you want to generate a new secret key?'):
            config = generate_config_file(config_file_path, database_file_path)
            click.echo(f"New secret: {config['SECRET_KEY']}")
            click.echo('Please restart the s4 server to apply the new secret key.')
    else:
        config = generate_config_file(config_file_path, database_file_path)
        click.echo(f"The s4 configuration has been completed! Secret: {config['SECRET_KEY']}")


@click.command()
@click.option('--version', is_flag=True, help='Returns the current version of s4 installed.')
@click.option('--configure', is_flag=True, help='Creates the base config and database file.')
def s4(version: bool, configure: bool) -> None:
    """
    The s4 command-line interface utility. Used for initial setup and other tasks.

    :param version: Returns the current version of s4 installed.
    :param setup: Creates the base config and database file.
    :return: None
    """
    if version:
        click.echo(f's4 v{__version__}')

    if configure:
        configure_s4()
