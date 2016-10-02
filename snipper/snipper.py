import os
from os import path
import json
import getpass
import glob
import logging
import sys
import re
import click

from api import Snippet
from repo import Repo

DEFAULT_SNIPPER_HOME = path.expanduser('~/.snippets')
DEFAULT_SNIPPER_CONFIG = path.join(DEFAULT_SNIPPER_HOME, 'config.json')
SNIPPET_METADATA_FILE = path.join(DEFAULT_SNIPPER_HOME, 'metadata.json')


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
            f.write(json.dumps(self.config, indent=4))

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
        click.secho('Configuration file not found. Plase give me your settings.', fg='red')
        init_snipper(home=home)

    config = SnipperConfig(config_file)
    config.set('snippet_home', home)

    ctx.obj = config

    api = Snippet()
    api.set_config(config)


def init_snipper(home):
    config_file = path.join(home, 'config.json')
    if path.exists(config_file) and not click.confirm('Config file already exist. Overwrite it'):
        return

    home = click.prompt('Where to keep snippets on local', default=home)
    username = click.prompt('Bitbucket username')
    click.secho(
        """Password using for authenticating to Bitbucket API.
        You can create an app password on Bitbucket account settings page.""",
        fg='green')

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


@cli.command(name='ls')
@pass_config
@click.pass_context
def list_snippets(context, config,  **kwargs):
    """ List local snippets """
    click.echo('List snippets')


@cli.command(name='update')
@pass_config
@click.pass_context
def update_local_snippets(context, config, **kwargs):
    """
    Update local snippets from Bitbucket.
    Pull existing snippets change and clone new snippets if exists.
    """

    api = Snippet()
    api.set_config(config)
    res = api.get_all()

    with open(path.join(SNIPPET_METADATA_FILE), 'w') as f:
        f.write(json.dumps(res))

    for item in res['values']:
        owner_username = item['owner']['username']
        snippet_id = item['id']
        repo_parent = path.join(DEFAULT_SNIPPER_HOME, owner_username)

        # Find snippet dirs which ends with specified snippet_id for checking
        # snippet cloned before

        # If directory name which end with snippet_id exist pull changes
        repo_path = glob.glob(path.join(repo_parent, '*{}'.format(snippet_id)))[0]
        if repo_path:
            Repo.pull(repo_path)
        else:
            # Clone repo over ssh (1)
            clone_url = item['links']['clone'][1]['href']
            clone_to = path.join(repo_parent, snippet_id)

            if item['title']:
                # Create dir name for snippet for clonning
                # Using title for best readablity(<slugified snippet_title>-<snippet_id>)
                slugified_title = re.sub('\W+', '-', item['title']).lower()
                clone_to = path.join(repo_parent, "{}-{}".format(slugified_title, snippet_id))


            Repo.clone(clone_url, clone_to=clone_to)


    click.secho('Local snippets updated and new snippets downloaded from Bitbucket', fg='green')


if __name__ == '__main__':
    cli()
