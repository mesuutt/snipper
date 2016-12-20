import os
from os import path
import json
import getpass
import glob
import logging
import sys
import pathlib

import pyperclip
import click
from prompt_toolkit import prompt
import configparser

from .api import SnippetApi
from .snippet import Snippet
from .completer import SnippetFilesCompleter
from . import utils

DEFAULT_SNIPPET_DIR = os.path.expanduser('~/.snippets')
DEFAULT_SNIPPER_CONFIG = os.path.expanduser('~/.snipperrc')

@click.group(context_settings={'help_option_names': ['-h', '--help']})
@click.option(
    '--config-file', '-c',
    default=DEFAULT_SNIPPER_CONFIG,
    type=click.Path(),
    help='Config file path: Default: {}'.format(DEFAULT_SNIPPER_CONFIG)
)
@click.pass_context
def cli(context, config_file):

    if not path.exists(config_file):
        click.secho('Configuration file not found. Plase give me your settings.', fg='red')
        init_snipper(config_file=config_file)

    # Create config with default values
    config = configparser.ConfigParser({
        'snippet_dir': DEFAULT_SNIPPET_DIR,
        'verbose': 'detailed',
        'auto_push': False,
        'default_filename': 'snippet.md',
    })

    # Overwrite config with user config.
    config.read(config_file)

    context.obj = config


def init_snipper(config_file):

    if path.exists(config_file) and not click.confirm('Config file already exist. Overwrite it'):
        return

    snippet_dir = click.prompt('Where to keep snippets', default=DEFAULT_SNIPPET_DIR)
    username = click.prompt('Bitbucket username')
    click.secho(
        """Password using for authenticating to Bitbucket API.
        You can create an App Password on Bitbucket settings page.
        """,
        fg='blue')

    password = getpass.getpass('Bitbucket Password:')

    # Create snippet home dir
    if not path.exists(snippet_dir):
        os.makedirs(snippet_dir)

    config = configparser.ConfigParser()
    config.read(config_file)

    config.set('snipper', 'snippet_dir', snippet_dir)
    config.set('snipper', 'username', username)
    config.set('snipper', 'password', password)
    config.set('snipper', 'verbose', 'detailed')

    config.write(open(config_file, 'w'))


@cli.command(name='ls')
@click.option('-v', 'verbose', flag_value='short', help='Provides short listing')
@click.option(
    '-vv',
    'verbose',
    default=True,
    flag_value='detailed',
    help='Provides the most detailed listing'
)
@click.pass_context
def list_snippets(context, verbose):
    """List local snippets"""

    config = context.obj

    config.set('snipper', 'verbose', verbose)

    with open(path.join(config.get('snipper', 'snippet_dir'), 'metadata.json'), 'r') as file:
        data = json.loads(file.read())
        for item in data['values']:

            if verbose == 'detailed':
                # Show files in snippet
                snippet = Snippet(config, item['owner']['username'], item['id'])
                snippet_path = snippet.get_path()

                if not snippet_path:
                    msg = '[{}] Snippet does not exist in file system. Please `pull` changes'
                    click.secho(msg.format(item['id']), fg='red')

                    continue

                onlyfiles = snippet.get_files()
                for file_name in onlyfiles:
                    click.secho(os.path.join(item['owner']['username'], snippet_path, file_name))


@cli.command(name='pull')
@click.pass_context
def pull_local_snippets(context):
    """
    Update local snippets from Bitbucket.
    Pull existing snippets change and clone new snippets if exists.
    """
    config = context.obj
    api = SnippetApi(config)
    res = api.get_all()

    with open(path.join(config.get('snipper', 'snippet_dir'), 'metadata.json'), 'w') as file:
        file.write(json.dumps(res))

    for item in res['values']:

        owner_username = item['owner']['username']
        snippet_id = item['id']
        repo_parent = path.join(config.get('snipper', 'snippet_dir'), owner_username)

        # Find snippet dirs which ends with specified snippet_id for checking
        # snippet cloned before

        # If directory name which end with snippet_id exist, pull changes
        matched_pats = glob.glob(path.join(repo_parent, '*{}'.format(snippet_id)))
        if matched_pats:
            Snippet.pull(matched_pats[0])
        else:
            Snippet.clone_by_snippet_id(context.obj, snippet_id)

    click.secho('Local snippets updated and new snippets downloaded from Bitbucket', fg='blue')


def _open_snippet_file(context, param, relative_path):
    """Open snippet file with default editor"""

    if not relative_path or context.resilient_parsing:
        return

    file_path = os.path.join(context.obj.get('snipper', 'snippet_dir'), relative_path)

    if os.path.exists(file_path):
        click.edit(filename=file_path)
    else:
        click.secho('File not exist. Exiting ...', fg='red')

    context.exit()

@cli.command(name='edit', help='Edit snippet file')
@click.option('--fuzzy', is_flag=True, default=True, help='Open fuzzy file finder')
@click.argument(
    'FILE_PATH',
    type=click.Path(),
    required=False, is_eager=True, expose_value=False,
    callback=_open_snippet_file
)
@click.pass_context
def edit_snippet_file(context, fuzzy, file_path=None):
    config = context.obj

    selected_file = prompt('[Add/Edit file] > ', completer=SnippetFilesCompleter(config))
    file_path = os.path.join(config.get('snipper', 'snippet_dir'), selected_file)

    click.edit(filename=file_path)

    parts = pathlib.Path(selected_file).parts
    repo_dir = os.path.join(config.get('snipper', 'snippet_dir'), parts[0], parts[1])

    commit_message = "{} updated".format(os.path.join(*parts[2:]))
    Snippet.commit(repo_dir, commit_message)

    if config.getboolean('snipper', 'auto_push'):
        click.secho('Pushing changes to Bitbucket', fg='blue')
        Snippet.push(repo_dir)


@cli.command(name='add', help='Create new snippet from file[s]/STDIN')
@click.option('--title', '-t', help='Snippet title', default='')
@click.option('--public', '-p', help='Make snippet public. Private by default', is_flag=True)
@click.option('--git', '-git', is_flag=True, help='Use git as scm. Mercurial by default')
@click.option('--copy-url', '-c', help='Copy resulting URL to clipboard', is_flag=True)
@click.option('--open', '-o', help='Open snippet URL on browser after create', is_flag=True)
@click.option('--paste', '-P', help='Create snippet from clipboard', is_flag=True)
@click.option('--file', '-f', type=click.Path(exists=True), help='Create snippet from file', multiple=True)
@click.argument('files', nargs=-1)
@click.pass_context
def add_snippet(context, files, **kwargs):

    config = context.obj

    content_list = utils.open_files(kwargs.get('file'))

    if files:
        # Read files given as positional parameter
        content_list.extend(utils.open_files(files))

    default_file_name = config.get('snipper', 'default_filename')

    if not sys.stdin.isatty():
        # Read from stdin if stdin has some data
        streamed_data = sys.stdin.read()
        content_list.append(('file', (default_file_name, streamed_data,),))

    if kwargs.get('paste'):
        # Read from clipboard
        clipboard_text = pyperclip.paste()
        if clipboard_text:
            content_list.append((default_file_name, clipboard_text))

    if not content_list:

        # click.edit() return None if user closes to editor without saving.
        content = click.edit()

        if content is None:
            click.secho('Empty content. Exiting', fg='red')
            sys.exit(1)

        if content == '':
            confirm = click.confirm('Content is empty. Create anyway?')
            if not confirm:
                sys.exit(1)

        content_list.append((default_file_name, content))

    scm = 'git' if kwargs.get('git') else 'hg'

    click.secho('Snippet creating...', fg='blue')

    api = SnippetApi(config)
    response = api.create_snippet(
        content_list,
        not kwargs.get('public', False),
        kwargs.get('title', None),
        scm,
    )

    if response.ok:
        snippet_metadata = response.json()

        Snippet.add_snippet_metadata(config, snippet_metadata)
        Snippet.clone_by_snippet_id(config, snippet_metadata['id'])

        click.secho('New snippets cloned from Bitbucket', fg='green')

        if kwargs.get('copy_url'):
            # Copy snippet url to clipboard
            pyperclip.copy(snippet_metadata['links']['html']['href'])
            click.secho('URL copied to clipboard', fg='green')



@cli.command(name='sync', help='Sync snippets with Bitbucket')
@click.pass_context
def sync_snippets(context):
    config = context.obj

    # glob is '*/*'
    files_depth_2 = glob.glob(os.path.join(config.get('snipper', 'snippet_dir'), '*', '*'))
    snippet_dirs = filter(lambda x: os.path.isdir(x), files_depth_2)

    for snippet_dir in snippet_dirs:
        Snippet.pull(snippet_dir)
        Snippet.push(snippet_dir)

if __name__ == '__main__':
    cli()
