import os
from os import path
import json
import getpass
import glob
import logging
import sys
import re
import click

from api import SnippetApi
from snippet import Snippet

DEFAULT_SNIPPER_HOME = path.expanduser('~/.snippets')
DEFAULT_SNIPPER_CONFIG = path.join(DEFAULT_SNIPPER_HOME, 'config.json')
SNIPPET_METADATA_FILE = path.join(DEFAULT_SNIPPER_HOME, 'metadata.json')


logger = logging.getLogger('snipper')
logger.setLevel(logging.DEBUG)  # TODO: set with --verbose param
ch = logging.StreamHandler(sys.stdout)
logger.addHandler(ch)


class SnipperConfig(object):
    verbose_short = 'short'
    verbose_detailed = 'detailed'

    def __init__(self, file):
        self.file = file
        self.config = {}
        self.config['verbose'] = self.verbose_short

        with open(self.file, 'r') as file:
            conf_content = json.loads(file.read())

        for key, value in conf_content.items():
            self.config[key] = value

    def get(self, key):
        return self.config[key]

    def set(self, key, value):
        self.config[key] = value

    def save_to_file(self):
        with open(self.file, 'w') as file:
            file.write(json.dumps(self.config, indent=4))

        logger.info('Config file updated: %s', self.file)

    def file_exists(self):
        return path.exists(self.file)


pass_config = click.make_pass_decorator(SnipperConfig)  # pylint: disable-msg=C0103


@click.group()
@click.option('--home', default=DEFAULT_SNIPPER_HOME, type=click.Path(), help='Snippet directory path. ({})'.format(DEFAULT_SNIPPER_HOME))
@click.option('--config-file', default=DEFAULT_SNIPPER_CONFIG, type=click.Path(), help='Snipper config.json file path. ({})'.format(DEFAULT_SNIPPER_CONFIG))
@click.pass_context
def cli(ctx, home, config_file, **kwargs): # pylint: disable-msg=W0613

    # Create a SnippetConfig object and remember it as as the context object.  From
    # this point onwards other commands can refer to it by using the
    # @pass_config decorator.

    if not path.exists(config_file):
        click.secho('Configuration file not found. Plase give me your settings.', fg='red')
        init_snipper(home=home)

    config = SnipperConfig(config_file)
    config.set('snippet_home', home)

    ctx.obj = config

    api = SnippetApi()
    api.set_config(config)


def init_snipper(home):
    config_file = path.join(home, 'config.json')
    if path.exists(config_file) and not click.confirm('Config file already exist. Overwrite it'):
        return

    home = click.prompt('Where to keep snippets on local', default=home)
    username = click.prompt('Bitbucket username')
    click.secho(
        """Password using for authenticating to Bitbucket API.
        You can create an App Password on Bitbucket settings page.
        """,
        fg='green')

    password = getpass.getpass('Bitbucket Password:')

    # Create snippet home dir
    if not path.exists(home):
        os.makedirs(home)

    # Create config file

    if not path.exists(config_file):
        with open(config_file, 'w+') as file:
            file.write('{}')

    config = SnipperConfig(config_file)
    config.set('snippet_home', home)
    config.set('username', username)
    config.set('password', password)
    config.set('verbose', SnipperConfig.verbose_detailed)

    config.save_to_file()


@cli.command(name='ls')
@click.option('-v', 'verbose', flag_value=SnipperConfig.verbose_short, help='Provides short listing')
@click.option(
    '-vv',
    'verbose',
    default=True,
    flag_value=SnipperConfig.verbose_detailed,
    help='Provides the most detailed listing'
)
@pass_config
@click.pass_context
def list_snippets(context, config, verbose, **kwargs):
    """List local snippets"""
    config.verbose = verbose
    print(verbose)
    with open(path.join(SNIPPET_METADATA_FILE), 'r') as file:
        data = json.loads(file.read())
        for item in data['values']:
            snippet_id = item['id']
            snippet_title = item['title']
            line = '[{id}] {title}'.format(
                id=snippet_id,
                title=snippet_title,
            )
            click.secho(line, fg='green')

            if verbose == SnipperConfig.verbose_detailed:
                # Show files in snippet
                snippet = Snippet(config, item['owner']['username'], snippet_id)

                onlyfiles = snippet.get_files()
                for file_name in onlyfiles:
                    click.secho("\t {}".format(file_name))


@cli.command(name='update')
@pass_config
@click.pass_context
def update_local_snippets(context, config, **kwargs):
    """
    Update local snippets from Bitbucket.
    Pull existing snippets change and clone new snippets if exists.
    """

    api = SnippetApi()
    api.set_config(config)
    res = api.get_all()

    with open(path.join(SNIPPET_METADATA_FILE), 'w') as file:
        file.write(json.dumps(res))

    for item in res['values']:
        owner_username = item['owner']['username']
        snippet_id = item['id']
        repo_parent = path.join(DEFAULT_SNIPPER_HOME, owner_username)

        # Find snippet dirs which ends with specified snippet_id for checking
        # snippet cloned before

        # If directory name which end with snippet_id exist pull changes
        matched_pats = glob.glob(path.join(repo_parent, '*{}'.format(snippet_id)))
        if matched_pats:
            Snippet.pull(matched_pats[0])
        else:
            # Clone repo over ssh (1)
            clone_url = item['links']['clone'][1]['href']
            clone_to = path.join(repo_parent, snippet_id)

            if item['title']:
                # Create dir name for snippet for clonning
                # Using title for readablity(<slugified snippet_title>-<snippet_id>)

                slugified_title = re.sub(r'\W+', '-', item['title']).lower()
                clone_to = path.join(repo_parent, "{}-{}".format(slugified_title, snippet_id))

            Snippet.clone(clone_url, clone_to=clone_to)

    click.secho('Local snippets updated and new snippets downloaded from Bitbucket', fg='blue')


if __name__ == '__main__':
    cli()
