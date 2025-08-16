import click
import json
import os
import sqlite3
#import threading

from flask import Flask, jsonify
from logging.config import dictConfig
from s4 import __version__
#from queue import Queue


app = Flask(__name__)


@click.command('version')
def ds4_version() -> None:
    """
    Prints the version of the s4 application.
    """
    click.echo(f's4 v{__version__}')


@app.route('/')
def index() -> str:
    return jsonify({
        'MESSAGE': 'Welcome to s4 server!'
        , 'DATABASE': app.config['DATABASE']
        , 'SECRET_KEY': app.config['SECRET_KEY']
    })


@app.route('/api/sql')
def sql() -> str | dict:
    return jsonify({
        'message': 'This is the SQL API endpoint.',
        'database': app.config['DATABASE']
    })


if __name__ == '__main__':
    print(os.path.join(app.instance_path, 'config.json'))

    # Configure the Flask app with the secret key from the config file
    try:
        config_file_path = os.path.join(app.instance_path, 'config.json')
        app.logger.info(f'Loading configuration from {config_file_path}')
        app.config.from_file(config_file_path, load=json.load)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        app.logger.warning('Configuration file not found or invalid. Using in-memory database and generating a default secret key.')
        app.config['SECRET_KEY'] = 's4'
        app.config['DATABASE'] = ':memory:'

    app.run()