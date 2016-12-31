import os
import json
import getpass
import sys
import configparser

import webbrowser
import pyperclip
import click
from prompt_toolkit import prompt

from .api import SnippetApi
from .snippet import Snippet
from .completer import SnippetFilesCompleter
from .repo import Repo
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
@click.option(
    '--no-color',
    default=False,
    is_flag=True,
    help='Don\'t colorize output',
)
@click.pass_context
def cli(context, config_file, no_color, **kwargs):

    if not os.path.exists(config_file):
        print('Configuration file not found. Plase give me your settings.')
        _init_snipper(config_file, not no_color)

    # Create config with default values
    config = configparser.ConfigParser({
        'snippet_dir': DEFAULT_SNIPPET_DIR,
        'verbose': 'detailed',
        'auto_push': 'yes',
        'default_filename': 'snippet.md',
        'colorize': 'no' if no_color else 'yes',
    })

    # Overwrite config with user config.
    config.read(config_file)

    # https protocol not supported because
    # user must give password every clone/pull/push.
    config.set('snipper', 'protocol', 'ssh')

    context.obj = config


def _init_snipper(config_file, colorize):

    if os.path.exists(config_file) and not click.confirm('Config file already exist. Overwrite it'):
        return

    snippet_dir = click.prompt('Where to keep snippets', default=DEFAULT_SNIPPET_DIR)
    username = click.prompt('Bitbucket username')
    password_help_text = '\n'.join([
        "You should give me a password for authenticating to Bitbucket API for accessing your snippets.",
        "You can create an app password that only permitted",
        "to snippets at settings page on bitbucket.org",
    ])

    utils.secho(colorize, password_help_text, fg='blue')

    password = getpass.getpass('App password:')

    # Create snippet home dir
    if not os.path.exists(snippet_dir):
        os.makedirs(snippet_dir)

    config = configparser.ConfigParser()
    config.read(config_file)

    config.add_section('snipper')

    config.set('snipper', 'snippet_dir', snippet_dir)
    config.set('snipper', 'username', username)
    config.set('snipper', 'password', password)
    config.set('snipper', 'verbose', 'detailed')
    config.set('snipper', 'colorize', 'True' if colorize else 'False')

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
    colorize = config.getboolean('snipper', 'colorize')

    config.set('snipper', 'verbose', verbose)

    with open(os.path.join(config.get('snipper', 'snippet_dir'), 'metadata.json'), 'r') as file:
        data = json.loads(file.read())

        for item in data['values']:

            if verbose == 'short':
                utils.secho(colorize, '[{}] {}'.format(item['id'], item['title']))

            elif verbose == 'detailed':
                # Show files in snippet
                snippet = Snippet(config, item)
                snippet_path = snippet.get_path()

                if not snippet.is_cloned():
                    msg = '[{}] {} \n Snippet does not exist. Please `pull` changes'
                    utils.secho(colorize, msg.format(item['id'], item['title']), fg='red')

                    continue

                onlyfiles = snippet.get_files()

                for file_name in onlyfiles:
                    utils.secho(colorize, os.path.join(snippet_path, file_name))

@cli.command(name='pull')
@click.pass_context
def pull_local_snippets(context):
    """
    Update local snippets from Bitbucket.
    Pull existing snippets change and clone new snippets if exists.
    """
    config = context.obj
    colorize = config.getboolean('snipper', 'colorize')

    api = SnippetApi(config)
    res = api.get_all()

    _update_metadata_file(config, res)

    for item in res['values']:
        snippet = Snippet(config, item)

        if snippet.is_cloned():
            utils.secho(colorize, '[{}] Pulling ...'.format(snippet.snippet_id), fg='blue')
            snippet.pull()
            snippet.update_dir_name()
        else:
            utils.secho(colorize, '[{}] Cloning ...'.format(snippet.snippet_id), fg='blue')
            snippet.clone()

    utils.secho(colorize, 'Local snippets updated and new snippets downloaded from Bitbucket', fg='blue')


def _open_snippet_file(context, param, relative_path):
    """Open snippet file with default editor"""

    config = context.obj
    colorize = config.getboolean('snipper', 'colorize')

    if not relative_path or context.resilient_parsing:
        return

    file_path = os.path.join(context.obj.get('snipper', 'snippet_dir'), relative_path)

    if os.path.exists(file_path):
        click.edit(filename=file_path)
    else:
        utils.secho(colorize, 'File not exist. Exiting ...', fg='red')

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
    colorize = config.getboolean('snipper', 'colorize')

    utils.secho(colorize, 'You can search and edit/add file with fuzzy search.', fg="yellow")
    utils.secho(colorize, 'Let\'s write some text. Press Ctrl+c for quit', fg="yellow")

    selected_file = prompt(u'> ', completer=SnippetFilesCompleter(config))
    file_path = os.path.join(config.get('snipper', 'snippet_dir'), selected_file)

    click.edit(filename=file_path)

    snippet_dir_name, _ = os.path.split(selected_file)
    repo_dir = os.path.join(config.get('snipper', 'snippet_dir'), snippet_dir_name)

    commit_message = u"{} updated".format(selected_file)
    Repo.commit(repo_dir, commit_message)

    if config.getboolean('snipper', 'auto_push'):
        utils.secho(colorize, 'Pushing changes to Bitbucket', fg='blue')
        Repo.push(repo_dir)


@cli.command(name='new', help='Create new snippet from file[s]/STDIN')
@click.option('--title', '-t', help='Snippet title', default='')
@click.option('--public', '-p', help='Make snippet public. Private by default', is_flag=True)
@click.option('--hg', '-hg', is_flag=True, help='Use mercurial. Git by default')
@click.option('--copy-url', '-c', help='Copy resulting URL to clipboard', is_flag=True)
@click.option('--open', '-o', help='Open snippet URL on browser after create', is_flag=True)
@click.option('--paste', '-P', help='Create snippet from clipboard', is_flag=True)
@click.option('--filename', '-f', help='Used when content read from STDIN or clipboard')
@click.argument('files', nargs=-1)
@click.pass_context
def new_snippet(context, files, **kwargs):

    config = context.obj
    colorize = config.getboolean('snipper', 'colorize')

    content_list = []

    if files:
        # Read files given as positional parameter
        content_list.extend(utils.open_files(files))

    default_filename = kwargs.get('filename', config.get('snipper', 'default_filename'))
    title = kwargs.get('title', None)

    if not sys.stdin.isatty():
        # Read from stdin if stdin has some data
        streamed_data = sys.stdin.read()
        content_list.append(('file', (default_filename, streamed_data,),))

    if kwargs.get('paste'):
        # Read from clipboard
        clipboard_text = pyperclip.paste()
        if clipboard_text:

            if not title:
                # if title not specified, make first 50 charecters of first line
                title = clipboard_text.split('\n')[0][:50]

            content_list.append(('file', (default_filename, clipboard_text)))

    if not content_list:

        # click.edit() return None if user closes to editor without saving.
        content = click.edit()

        if content is None:
            utils.secho(colorize, 'Empty content. Exiting', fg='red')
            sys.exit(1)

        if content == '':
            confirm = click.confirm('Content is empty. Create anyway?')
            if not confirm:
                sys.exit(1)

        if not title:
            # if title not specified, make first 50 charecters of first line
            title = content.split('\n')[0][:50]

        content_list.append(('file', (default_filename, content)))

    scm = 'hg' if kwargs.get('hg') else 'git'

    utils.secho(colorize, 'Snippet creating...', fg='blue')

    api = SnippetApi(config)
    response = api.create_snippet(
        content_list,
        not kwargs.get('public', False),
        title,
        scm,
    )

    if response.ok:
        snippet = Snippet(config, response.json())

        # Add new created snippet metadata to file
        metadata_file = os.path.join(config.get('snipper', 'snippet_dir'), 'metadata.json')
        with open(metadata_file, 'r+') as file:
            metadata = json.loads(file.read())
            file.seek(0)
            metadata['values'].append(response.json())
            file.write(json.dumps(metadata))

        snippet.clone()

        utils.secho(colorize, 'Created snippet cloned from Bitbucket', fg='green')

        snipper_url = snippet.data['links']['html']['href']
        if kwargs.get('copy_url'):
            # Copy snippet url to clipboard
            pyperclip.copy(snipper_url)
            utils.secho(colorize, 'URL copied to clipboard', fg='green')

        if kwargs.get('open'):
            webbrowser.open_new_tab(snipper_url)

        snippet.show_details()

@cli.command(name='sync', help='Sync snippets with Bitbucket')
@click.argument('snippet_id', nargs=1, required=False)
@click.pass_context
def sync_snippets(context, **kwargs):
    config = context.obj
    colorize = config.getboolean('snipper', 'colorize')
    snippet_id = kwargs.get('snippet_id')

    api = SnippetApi(config)

    utils.secho(colorize, 'Downloading snippet meta data from Bitbucket', fg='green')
    res = api.get_all()

    _update_metadata_file(config, res)

    with open(os.path.join(config.get('snipper', 'snippet_dir'), 'metadata.json'), 'r') as file:
        data = json.loads(file.read())
        snippet = None

        for item in data['values']:

            if snippet_id and item['id'] != snippet_id:
                continue

            # Show files in snippet
            snippet = Snippet(config, item)

            if not snippet.is_cloned():
                # If snippet not exist in local, clone snippet
                utils.secho(colorize, '[{}] {}'.format(item['id'], item.get('title', 'Untitled snippet')), fg='blue')
                snippet.clone()
            else:
                # Commit changes if exist before pull new changes from remote.
                snippet.commit()

                utils.secho(colorize, '[{}]: Syncing snippet...'.format(item['id']), fg='blue')
                snippet.pull()
                snippet.push()
                snippet.update_dir_name()

        if snippet_id and not snippet:
            utils.secho(colorize, 'Snippet with given id not found: {}'.format(snippet_id), fg='yellow')


def _update_metadata_file(config, data):
    """Update local metadata file that keeps all snippet's data"""

    with open(os.path.join(config.get('snipper', 'snippet_dir'), 'metadata.json'), 'w') as file:
        file.write(json.dumps(data))


if __name__ == '__main__':
    cli()

