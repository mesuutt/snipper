import os
from os import path
import json
import getpass
import logging
import sys

import click

from api import Snippet

DEFAULT_SNIPPER_HOME = path.expanduser('~/.snippets')
DEFAULT_SNIPPER_CONFIG = path.join(DEFAULT_SNIPPER_HOME, 'config.json')


logger = logging.getLogger('snipper')
logger.setLevel(logging.DEBUG) #TODO: set with --verbose param
ch = logging.StreamHandler(sys.stdout)
logger.addHandler(ch)


class SnipperConfig(object):

    def __init__(self, file):
        self.file = file
        self.config = {}

        with open(self.file, 'r') as f:
            conf_content = json.loads(f.read())

        for key, value in conf_content.items():
            self.config[key] = value

    def get(self, key):
        return self.config[key]

    def set(self, key, value):
        self.config[key] = value

    def save_to_file(self):
        with open(self.file, 'w') as f:
            f.write(json.dumps(self.config))

        logger.info('Config file updated: {}'.format(self.file))

    def file_exists(self):
        return path.exists(self.file)

pass_config = click.make_pass_decorator(SnipperConfig)


@click.group()
@click.option('--home', default=DEFAULT_SNIPPER_HOME, type=click.Path())
@click.option('--config-file', default=DEFAULT_SNIPPER_CONFIG, type=click.Path())
@click.pass_context
def cli(ctx, home, config_file, **kwargs):

    # Create a SnippetConfig object and remember it as as the context object.  From
    # this point onwards other commands can refer to it by using the
    # @pass_config decorator.
    if not path.exists(config_file):
        init_snipper(home=home)

    config = SnipperConfig(config_file)
    config.set('snippet_home', home)

    ctx.obj = config

    api = Snippet()
    api.set_config(config)


def init_snipper(home):
    config_file = path.join(home, 'config.json')

    home = click.prompt('Where to keep snippets on local', default=home)
    username = click.prompt('Bitbucket username')
    click.echo('Password using for authenticating to Bitbucket API. You can create an app password for on Bitbucket account settings page.')
    password = getpass.getpass('Bitbucket Password:')

    # Create snippet home dir
    if not path.exists(home):
        os.makedirs(home)

    # Create config file

    if not path.exists(config_file):
        with open(config_file, 'w+') as f:
            f.write('{}')


    config = SnipperConfig(config_file)
    config.set('snippet_home', home)
    config.set('username', username)
    config.set('password', password)
    config.save_to_file()

@cli.command(name='init')
@click.option('--home', default=DEFAULT_SNIPPER_HOME, type=click.Path())
def init(home, **kwargs):
    init_snipper(home)



@cli.command(name='ls')
@pass_config
@click.pass_context
def list_snippets(context, config,  **kwargs):

    click.echo('List snippets')





if __name__ == '__main__':
    cli()
