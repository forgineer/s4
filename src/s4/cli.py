import click
import os
import secrets
import sqlite3

from s4 import __version__


# Define the current working directory, config file, database file, and path
CURRENT_WORKING_DIRECTORY: str = os.getcwd()
CONFIG_FILE_NAME: str = 'config.py'
CONFIG_FILE_PATH: str = os.path.join(CURRENT_WORKING_DIRECTORY, CONFIG_FILE_NAME)
DATABASE_FILE_NAME: str = 's4.db'
DATABASE_FILE_PATH: str = os.path.join(CURRENT_WORKING_DIRECTORY, DATABASE_FILE_NAME)


def setup_s4() -> None:
    """
    Creates a config and database file with a generated SECRET_KEY value for Flask.

    :return: None
    """
    if os.path.exists(CONFIG_FILE_PATH):
        click.echo(f"The configuration file '{CONFIG_FILE_NAME}' already exists. Setup aborted. Run the server using 'python -m s4.server'.")
        return

    # Define Flask secret key and database file path
    secret_key: str = secrets.token_urlsafe(32)
    
    try:
        s4_db: sqlite3.Connection = sqlite3.connect(DATABASE_FILE_PATH)
        s4_db.cursor().execute('CREATE TABLE IF NOT EXISTS s4_secrets (id INTEGER PRIMARY KEY, secret_name TEXT, secret TEXT)')
        s4_db.cursor().execute('INSERT INTO s4_secrets (secret_name, secret) VALUES (?, ?)', ('s4_secret_key', secret_key))
        s4_db.commit()
    except sqlite3.Error as e:
        click.echo(f"An error occurred while creating the database: {e}")
        return

    with open(CONFIG_FILE_PATH, 'w', ) as f:
        f.write(f"SECRET_KEY = '{secret_key}'\n")
        f.write(f"DATABASE_FILE_PATH = '{DATABASE_FILE_PATH}'\n")

    click.echo("The s4 configuration has been completed! You can now run the server using 'python -m s4.server'.")


@click.command()
@click.option('--version', is_flag=True, help='Returns the current version of s4 installed.')
@click.option('--setup', is_flag=True, help='Creates the base config and database file.')
def s4(version: bool, setup: bool) -> None:
    """
    The s4 command-line interface utility. Used for initial setup and other tasks.

    :param version: Returns the current version of s4 installed.
    :param setup: Creates the base config and database file.
    :return: None
    """
    if version:
        click.echo(f's4 v{__version__}')

    if setup:
        setup_s4()
