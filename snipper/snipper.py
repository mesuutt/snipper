import os
import json
import getpass
import logging
import sys

import click

from api import Snippet

DEFAULT_SNIPPET_HOME = '~/.snippets'

logger = logging.getLogger('snipper')
logger.setLevel(logging.DEBUG) #TODO: set with --verbose param
ch = logging.StreamHandler(sys.stdout)
logger.addHandler(ch)


class SnipperConfig(object):

    def __init__(self, file):
        self.file = os.path.expanduser(file)
        self.config = {}
        conf_content = json.loads(open(self.file, 'r').read())

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

pass_config = click.make_pass_decorator(SnipperConfig)


@click.group()
@click.option('--home', default=DEFAULT_SNIPPET_HOME, type=click.Path())
@click.option('--config-file', default='{}/config.json'.format(DEFAULT_SNIPPET_HOME), type=click.Path())
@click.pass_context
def cli(ctx, home, config_file):

    if  not os.path.exists(config_file):
        click.echo('You are using snipper first time?')
        click.echo('Call `snipper init` command')
        ctx.exit()

    # Create a SnippetConfig object and remember it as as the context object.  From
    # this point onwards other commands can refer to it by using the
    # @pass_config decorator.
    config = SnipperConfig(config_file)
    config.set('snippet_home', home)

    ctx.obj = config

    api = Snippet()
    api.set_config(config)


@cli.command(name='init')
@pass_config
def init_snipper(config):

    home = click.prompt('Where to keep snippets on local', default=DEFAULT_SNIPPET_HOME)
    username = click.prompt('Bitbucket username')
    click.echo('Password using for authenticating to Bitbucket API. You can create an app password for on Bitbucket account settings page.')
    password = getpass.getpass('Bitbucket Password:')

    config.set('snippet_home', home)
    config.set('username', username)
    config.set('password', password)
    config.save_to_file()


@cli.command(name='ls')
@pass_config
def list_snippets(config,  **kwargs):
    click.echo('List snippets')





if __name__ == '__main__':
    cli()