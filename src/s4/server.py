import click
import functools
import json
import os
import secrets
import sqlite3
#import threading

from flask import Flask, jsonify, request
from logging.config import dictConfig
from s4 import __version__
from typing import Literal
#from queue import Queue


def generate_secret_key() -> str:
    """
    Generates a random secret key for Flask and s4 DB access.

    :return: A securely generated secret key.
    """
    return secrets.token_urlsafe(32)


def create_config_file(instance_path: str) -> dict:
    """
    Create a configuration file for s4 with a random secret key and database file path.
    
    :param instance_path: The path where the configuration file will be saved.
    :return: A dictionary containing the configuration settings.
    """
    _config: dict = {
        'SECRET_KEY': generate_secret_key(),
        'DATABASE': os.path.join(instance_path, 's4.db')
    }

    with open(os.path.join(instance_path, 'config.json'), "w") as file:
        json.dump(_config, file, indent=4)
    
    return _config


def read_config_file(instance_path: str) -> dict | bool:
    """
    Read the configuration file for s4 with a random secret key and database file path.
    
    :param instance_path: The path where the configuration file will be saved.
    :return: A dictionary containing the configuration settings.
    """
    try:
        with open(os.path.join(instance_path, 'config.json'), "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return False
    

def create_app(log_level: Literal['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'] = 'INFO') -> Flask:
    """
    Create and configure the Flask application.

    :return: Configured Flask application instance.
    """
    # Configure logging
    dictConfig({
        'version': 1,
        'formatters': {
            'default': {
                'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
            }
        },
        'handlers': {
            'wsgi': {
                'class': 'logging.StreamHandler',
                'stream': 'ext://flask.logging.wsgi_errors_stream',
                'formatter': 'default'
            }
        },
        'root': {
            'level': log_level,
            'handlers': ['wsgi']
        }
    })


    def dict_factory(cursor: sqlite3.Cursor, row: tuple) -> dict:
        """
        Convert a row from the database cursor into a dictionary.
        
        :param cursor: The database cursor.
        :param row: The row to convert.
        :return: A dictionary representing the row.
        """
        fields = [column[0] for column in cursor.description]
        return {key: value for key, value in zip(fields, row)}


    # Create and configure the app
    app = Flask(__name__)


    @app.before_request
    def validate_key() -> None:
        """
        Validate the secret key before processing any request.

        :return: None.
        """
        if request.headers.get('s4-Secret-Key', None) != app.config['SECRET_KEY']:
            return jsonify({
                'error': 'Invalid secret key.'
            }), 401


    @app.route('/')
    def verify_connection() -> str:
        return 'Welcome to s4! The server is running!'


    @app.route('/api/sql', methods=['POST'])
    def sql() -> dict:
        app.logger.debug(f'Request JSON: {request.json}')

        _sql: str | bool = request.json.get('sql', False)

        if not _sql:
            return jsonify({
                'error': 'No SQL query provided.'
            }), 400
        
        conn: sqlite3.Connection = sqlite3.connect(app.config['DATABASE'])
        conn.row_factory = dict_factory
        results: list[dict] = []
        response: dict = {}
        cursor: sqlite3.Cursor = conn.cursor()

        try:
            cursor.execute(_sql)
            conn.commit()
            results = cursor.fetchall()

            cursor.close()
            conn.close()

            response = {
                'sqlResponse': results
            }

            return response, 200
        except sqlite3.Error as e:
            cursor.close()
            conn.close()
            app.logger.error(f'SQL Error: {str(e)}')

            return jsonify({
                'error': str(e)
            }), 500

    return app


@click.command()
@click.option('--version', is_flag=True, help='Returns the current version of s4 installed.')
@click.option('--configure', is_flag=True, help='Configures the s4 server.')
@click.option('--run', is_flag=True, help='Runs the s4 server.')
@click.option('--log-level', type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']), default='INFO', help='Sets the log level for s4 server.')
@click.option('--in-memory', is_flag=True, help='Runs the s4 server with an in-memory database.')
@click.option('--port', type=int, default=5000, help='Port to run the s4 server on. Default is 5000.')
def cli(version: bool, configure: bool, run: bool, log_level: str, in_memory: bool, port: int) -> None:
    """
    The s4 command-line interface utility. Used for initial setup and other tasks.

    :param version: Returns the current version of s4 installed.
    :param run: Starts the s4 server.
    :return: None
    """
    if version:
        click.echo(f's4 v{__version__}')

    # Construct the app and instance path
    app: Flask = create_app(log_level)
    instance_path: str = app.instance_path

    if not os.path.exists(instance_path):
        os.makedirs(instance_path)

    config: dict | bool = read_config_file(instance_path)   

    if configure:
        if config:
            if click.confirm('Configuration file already exists. Do you want generate a new secret key and overwrite it?'):
                config = create_config_file(instance_path)
                click.echo(f"Configuration re-created: {config}")
                click.echo('Please restart the s4 server to apply the new secret key.')
        else:
            config = create_config_file(instance_path)
            click.echo(f"Configuration created: {config}")
    
    if run:
        if not config:
            click.echo('No configuration file found. Using in-memory database with default secret key. Please run "s4 --configure" to create a configuration file (recommended).')
            config = {
                'SECRET_KEY': 's4',
                'DATABASE': ':memory:'
            }

        app.config.from_mapping(config)

        if in_memory:
            app.config['DATABASE'] = ':memory:'
            click.echo('Using in-memory database for this session.')

        app.run(port=port)
