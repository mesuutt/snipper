import os
import getpass
import sys
import configparser
import re
import glob
import shutil

import click
import pyperclip
import webbrowser
from prompt_toolkit import prompt

from .api import SnippetApi
from .snippet import Snippet
from .completers import SnippetFileCompleter, SnippetDirCompleter, ValidateSnippetDir, ValidateSnippetFile
from .repo import Repo
from . import utils

DEFAULT_SNIPPET_DIR = os.path.expanduser('~/.snippets')
DEFAULT_SNIPPER_CONFIG = os.path.expanduser('~/.snipperrc')


@click.group(context_settings={'help_option_names': ['-h', '--help']})
@click.option(
    '--config', '-C', 'config_file',
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
def cli(ctx, config_file, no_color, **kwargs):

    if not os.path.exists(config_file):
        print('Configuration file not found. Plase give me your settings.')
        _init_snipper(config_file, not no_color)

    # Create config with default values
    config = configparser.ConfigParser({
        'snippet_dir': DEFAULT_SNIPPET_DIR,
        'auto_push': 'yes',
        'default_filename': 'file.txt',
        'colorize': 'no' if no_color else 'yes',
    })

    # Overwrite config with user config.
    config.read(config_file)

    # https protocol not supported because
    # user must give password every clone/pull/push.
    config.set('snipper', 'protocol', 'ssh')

    # Read useraname/password from env vars not exist in config file
    if not config.has_option('snipper', 'username') and os.environ.get('SNIPPER_USERNAME'):
        config.set('snipper', 'username', os.environ['SNIPPER_USERNAME'])

    if not config.has_option('snipper', 'password') and os.environ.get('SNIPPER_PASSWORD'):
        config.set('snipper', 'password', os.environ['SNIPPER_PASSWORD'])

    ctx.obj = config


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
    config.set('snipper', 'colorize', 'yes' if colorize else 'no')

    config.write(open(config_file, 'w'))


@cli.command(name='ls')
@click.option('-v', 'verbose', default=True, flag_value='short', help='Provides short listing')
@click.option(
    '-vv',
    'verbose',
    flag_value='detailed',
    help='Provides the most detailed listing'
)
@click.pass_context
def list_snippets(ctx, verbose):
    """List local snippets"""
    config = ctx.obj
    colorize = config.getboolean('snipper', 'colorize')

    data = utils.read_metadata(config)

    long_file_list = []
    for item in data['values']:
        snippet = Snippet(config, item)

        if not snippet.is_exists():
            msg = '[{}] Snippet does not exist in snippet directory. Please `pull` or `sync`'.format(item['id'])
            utils.secho(colorize, msg, fg='blue')

            continue

        if verbose == 'short':
            utils.secho(colorize, '[{}] {}'.format(item['id'], item['title']), fg='blue')

        elif verbose == 'detailed':
            # Show files in snippet
            onlyfiles = snippet.get_files()

            for file_name in onlyfiles:
                snippet_path = snippet.get_path()
                long_file_list.append(os.path.join(snippet_path, file_name))

    if long_file_list:
        click.echo_via_pager('\n'.join(long_file_list))


@cli.command(name='pull')
@click.pass_context
def pull_local_snippets(ctx):
    """Update local snippets from Bitbucket.

    Pull changes of existing snippets and clone new snippets.
    """
    config = ctx.obj
    colorize = config.getboolean('snipper', 'colorize')

    api = SnippetApi(config)
    res = api.get_all()

    utils.update_metadata(config, res)

    for item in res['values']:
        snippet = Snippet(config, item)

        if snippet.is_exists():
            utils.secho(colorize, '[{}] Pulling ...'.format(snippet.snippet_id), fg='blue')
            snippet.pull()
            snippet.update_dir_name()
        else:
            utils.secho(colorize, '[{}] Cloning ...'.format(snippet.snippet_id), fg='blue')
            snippet.clone()

    utils.secho(colorize, 'Local snippets updated and new snippets downloaded from Bitbucket', fg='blue')


def _edit_snippet_file(ctx, param, relative_path):
    """Open snippet file with default editor"""
    config = ctx.obj
    colorize = config.getboolean('snipper', 'colorize')

    if not relative_path or ctx.resilient_parsing:
        return

    file_path = os.path.join(config.get('snipper', 'snippet_dir'), relative_path)

    if os.path.exists(file_path):
        click.edit(filename=file_path)
    else:
        utils.secho(colorize, 'File not exist. Exiting ...', fg='red')

    ctx.exit()


@cli.command(name='edit', help='Edit snippet file')
@click.option('--fuzzy', is_flag=True, default=True, help='Open fuzzy file finder')
@click.argument(
    'FILE_PATH',
    type=click.Path(),
    required=False, is_eager=True, expose_value=False,
    callback=_edit_snippet_file
)
@click.pass_context
def edit_snippet_file(ctx, fuzzy, file_path=None):
    config = ctx.obj
    colorize = config.getboolean('snipper', 'colorize')

    utils.secho(colorize, 'Select a file for edit with fuzzy search.', fg="yellow")
    utils.secho(colorize, 'Let\'s write some text. Press Ctrl+c for quit', fg="yellow")

    selected_file = prompt(
        u'> ',
        completer=SnippetFileCompleter(config),
        validator=ValidateSnippetFile(config)
    )
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
@click.argument('files', nargs=-1, type=click.Path(exists=True))
@click.pass_context
def new_snippet(ctx, files, **kwargs):

    config = ctx.obj
    colorize = config.getboolean('snipper', 'colorize')
    content_list = []

    if files:
        # Read files given as positional parameter
        content_list.extend(utils.open_files(files))

    # if filename is not specified, it is exist everytime as None
    # so kwargs.get('filename', default_val) not working
    filename = kwargs.get('filename')
    if not filename:
        filename = config.get('snipper', 'default_filename')

    title = kwargs.get('title', None)

    # Read from STDIN of clipboard but not both
    if not sys.stdin.isatty():
        # Read from stdin if stdin has some data
        streamed_data = sys.stdin.read()
        content_list.append(('file', (filename, streamed_data,),))
        utils.secho(colorize, 'New file created from STDIN', fg='blue')
    elif kwargs.get('paste'):
        # Read from clipboard
        clipboard_text = pyperclip.paste()
        if clipboard_text:

            if not title:
                # if title not specified, make title first 50 charecters of first line
                title = clipboard_text.split('\n')[0][:50]

            content_list.append(('file', (filename, clipboard_text)))
            utils.secho(colorize, 'New file created from clipboard content', fg='blue')
        else:
            utils.secho(colorize, 'Clipboard is empty, ignoring', fg='yellow')

    if not content_list:

        # click.edit() return None if user closes to editor without saving.
        content = click.edit()

        if content is None:
            utils.secho(colorize, 'Empty content. Exiting', fg='red', err=True)
            sys.exit(1)

        if content == '':
            confirm = click.confirm('Content is empty. Create anyway?')
            if not confirm:
                sys.exit(1)

        if not title:
            # if title not specified, make first 50 charecters of first line
            title = content.split('\n')[0][:50]

        content_list.append(('file', (filename, content)))

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

        # Update metadata file
        metadata = utils.read_metadata(config)
        metadata['values'].append(response.json())
        utils.update_metadata(config, metadata)

        snippet = Snippet(config, response.json())
        snippet.clone()

        utils.secho(colorize, 'Created snippet cloned from Bitbucket', fg='green')

        snipper_url = snippet.data['links']['html']['href']
        if kwargs.get('copy_url'):
            # Copy snippet url to clipboard
            pyperclip.copy(snipper_url)
            utils.secho(colorize, 'URL copied to clipboard', fg='green')

        if kwargs.get('open'):
            webbrowser.open_new_tab(snipper_url)

        print(snippet.get_detail_for_print())


@cli.command(name='sync', help='Sync snippets with Bitbucket')
@click.argument('snippet_id', nargs=1, required=False)
@click.pass_context
def sync_snippets(ctx, **kwargs):
    config = ctx.obj
    colorize = config.getboolean('snipper', 'colorize')
    snippet_id = kwargs.get('snippet_id')

    api = SnippetApi(config)

    utils.secho(colorize, 'Downloading snippet meta data from Bitbucket', fg='green')
    data = api.get_all()

    utils.update_metadata(config, data)

    snippet = None
    for item in data['values']:

        if snippet_id and item['id'] != snippet_id:
            continue

        # Show files in snippet
        snippet = Snippet(config, item)

        if not snippet.is_exists():
            # If snippet not exist in local, clone snippet
            utils.secho(colorize, '[{}] {}'.format(item['id'], item.get('title', 'Untitled snippet')), fg='blue')
            snippet.clone()
        else:
            # Commit changes if exist before pull new changes from remote.
            snippet.commit()

            utils.secho(colorize, '[{}]: Syncing snippet...'.format(item['id']), fg='blue')
            snippet.sync()
            snippet.update_dir_name()

    if snippet_id and not snippet:
        utils.secho(colorize, 'Snippet with given id not found: {}'.format(snippet_id), fg='yellow')


@cli.command(name='add', help='Add file[s] to snippet')
@click.argument('to', nargs=1, required=False)
@click.argument('files', nargs=-1, type=click.Path(exists=True))
@click.option('--filename', '-f', help='Used when content read from STDIN or clipboard')
@click.option('--open', '-o', help='Open snippet URL on browser after file added', is_flag=True)
@click.option('--paste', '-P', help='Read content from clipboard', is_flag=True)
@click.option('--copy-url', '-c', help='Copy snippet URL to clipboard', is_flag=True)
@click.pass_context
def add_to_snippet(ctx, files, **kwargs):
    config = ctx.obj
    colorize = config.getboolean('snipper', 'colorize')
    selected_snippet_dirname = None

    if not kwargs.get('to'):
        utils.secho(colorize, 'Select snippet to add file with fuzzy search.', fg="yellow")
        utils.secho(colorize, 'Let\'s write some text. Press Ctrl+c for quit', fg="yellow")
        selected_snippet_dirname = prompt(
            u'> ',
            completer=SnippetDirCompleter(config),
            validator=ValidateSnippetDir(config)
        )

    if not selected_snippet_dirname:
        selected_snippet_dirname = kwargs.get('to', '')

    snippet_dir_path_regex = re.search('(?:.*)?([\w]{5})$', selected_snippet_dirname)
    if not snippet_dir_path_regex:
        utils.secho(colorize, 'Give me path of snippet directory or snippet id', fg='red', err=True)
        utils.secho(colorize, 'Existing snippet directories:', fg='blue')

        _print_snippet_dirs(config, relative=True)
        sys.exit(1)

    snippet_id = snippet_dir_path_regex.group(1)

    if not sys.stdin.isatty() and kwargs.get('paste'):
        utils.secho(colorize, 'You cannot use STDIN and clipboard both for creating snippet file.', fg='red', err=True)
        utils.secho(colorize, 'Please pipe content from STDIN or use -P for getting content from clipboard but not both.', fg='red', err=True)
        sys.exit(1)

    data = utils.read_metadata(config)
    repo_parent = config.get('snipper', 'snippet_dir')
    snippet = None

    for item in data['values']:
        if not snippet_id == item['id']:
            continue

        matched_path = glob.glob(os.path.join(repo_parent, '*{}'.format(snippet_id)))
        if not matched_path:
            utils.secho(colorize, '[{}] Snippet directory not found.'.format(snippet_id), fg='red', err=True)
            sys.exit(1)

        snippet_dir = matched_path[0]
        snippet = Snippet(config, item)
        break

    if not snippet:
        utils.secho(colorize, 'Snippet not found. Exiting!'.format(snippet_id), fg='red', err=True)
        sys.exit(1)

    # if filename is not specified, it is exist everytime as None
    # so kwargs.get('filename', default_val) not working
    filename = kwargs.get('filename')
    if not filename:
        filename = config.get('snipper', 'default_filename')

    file_path = utils.get_incremented_file_path(os.path.join(snippet_dir, filename))

    if not sys.stdin.isatty():
        # Read from STDIN
        streamed_data = sys.stdin.read()

        with open(file_path, 'w') as file:
            file.write(streamed_data)
            utils.secho(colorize, 'File created from STDIN: {}'.format(file_path), fg='blue')

    elif kwargs.get('paste'):
        # Read from clipboard
        clipboard_text = pyperclip.paste()

        if clipboard_text:
            with open(file_path, 'w') as file:
                file.write(streamed_data)
                utils.secho(colorize, 'File created from clipboard content: {}'.format(file_path), fg='blue')
        else:
            utils.secho(colorize, 'Clipboard is empty, ignoring', fg='yellow')
    else:
        # Open editor
        new_file_content = click.edit()
        if new_file_content is None:
            utils.secho(colorize, 'Empty content. Exiting', fg='red', err=True)
            sys.exit(1)

        if new_file_content == '':
            confirm = click.confirm('Content is empty. Create anyway?')
            if not confirm:
                sys.exit(1)

        with open(file_path, 'w') as file:
            file.write(new_file_content)
            utils.secho(colorize, 'File created: {}'.format(file_path), fg='blue')

    for file in files:
        # Copy given files to snippet
        utils.secho(colorize, '{} added to snippet'.format(file), fg='blue')
        shutil.copy(file, snippet_dir)
        utils.secho(colorize, 'File added: {}'.format(file), fg='blue')

    snippet.commit()

    if config.getboolean('snipper', 'auto_push'):
        utils.secho(colorize, 'Snippet pushing to Bitbucket', fg='blue')
        snippet.push()


def _print_snippet_dirs(config, relative=True):
    colorize = config.getboolean('snipper', 'colorize')
    data = utils.read_metadata(config)

    for item in data['values']:
        # Show files in snippet
        snippet = Snippet(config, item)
        path = snippet.get_slugified_dirname() if relative else snippet.get_path()
        utils.secho(colorize, path, fg='yellow')


if __name__ == '__main__':
    cli()
