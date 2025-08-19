import click
import json
import os
import secrets
import sqlite3
#import threading

from flask import Flask, g, jsonify, request, session
from logging.config import dictConfig
from s4 import __version__
from typing import Literal
#from queue import Queue


def create_config_file(instance_path: str) -> dict:
    """
    Create a configuration file for s4 with a random secret key and database file path.
    
    :param instance_path: The path where the configuration file will be saved.
    :return: A dictionary containing the configuration settings.
    """
    _config: dict = {
        'SECRET_KEY': secrets.token_urlsafe(32),  # Generate a random secret key
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
        Convert rows from the database cursor into dictionaries.
        
        :param cursor: The database cursor.
        :param row: The row to convert.
        :return: A dictionary representing the row(s).
        """
        fields = [column[0] for column in cursor.description]
        return {key: value for key, value in zip(fields, row)}
    

    def s4_sql(sql: str) -> dict:
        """
        Execute a SQL query and return the results.

        :param sql: The SQL query to execute.
        :return: A dictionary containing the results of the SQL query.
        """
        cursor: sqlite3.Cursor = g.db.cursor()

        try:
            cursor.execute(sql)
            g.db.commit()
            results = cursor.fetchall()
            return {'sqlResponse': results}
        except sqlite3.Error as e:
            app.logger.error(f'SQL Error: {str(e)}')
            return {'error': str(e)}
        finally:
            cursor.close()


    # Create and configure the app
    app = Flask(__name__)


    @app.before_request
    def validate() -> None:
        """
        Validate the secret key before processing any request.

        :return: None.
        """
        if request.headers.get('s4-Secret-Key', None) != app.config['SECRET_KEY']:
            return jsonify({
                'error': 'Invalid secret key.'
            }), 401

        if 'db' not in g:
            g.db = sqlite3.connect(app.config['DATABASE'])
            g.db.row_factory = dict_factory


    @app.route('/api/connect')
    def connect() -> str:
        """
        Verify the connection to the s4 server.
        
        :return: A success message.
        """
        return 'Connection to s4 server established successfully!'


    @app.route('/api/sql', methods=['POST'])
    def sql() -> dict:
        app.logger.debug(f'Request JSON: {request.json}')

        _sql: str | bool = request.json.get('sql', False)
        
        return s4_sql(_sql) if _sql else {'error': 'No SQL query provided.'}


    @app.teardown_appcontext
    def teardown(exception: Exception) -> None:
        """
        Close the database connection after processing a request.

        :param exception: The exception that occurred during request processing.
        :return: None.
        """
        db: sqlite3.Connection = g.pop('db', None)

        if db is not None:
            db.close()
            app.logger.debug('Database connection closed.')

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

    :param version: If set, prints the current version of s4.
    :param configure: If set, configures the s4 server.
    :param run: If set, runs the s4 server.
    :param log_level: Sets the log level for the s4 server.
    :param in_memory: If set, runs the s4 server with an in-memory database.
    :param port: The port to run the s4 server on. Default is 5000.
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
