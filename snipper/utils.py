import os
import re
import sys
import json
from subprocess import Popen, PIPE

import click

if sys.version_info >= (3, 3):
    from subprocess import DEVNULL
else:
    DEVNULL = open(os.devnull, 'w')


def open_files(filelist):
    """Open files for upload"""
    files = []
    for file_path in filelist:
        if not os.path.exists(file_path):
            continue

        filename = os.path.basename(file_path)
        files.append(('file', (filename, open(file_path, 'rb'))))

    return files


def slugify(text):
    return re.sub(r'\W+', '-', text).lower()


def run_command(cmd):
    """Run command on shell"""
    # This commands will run in background.
    # So can return before process completed.
    process = Popen(cmd, shell=True, stderr=PIPE, stdout=DEVNULL, universal_newlines=True)

    # If you want to sure process completed use p.wait()
    # If you will check process same as `process.stderr.read()` process will wait automatically.

    return process


def secho(colorize, text, **kwargs):
    """Print text colorized or not colorized"""
    if not colorize:
        kwargs.pop('fg', None)
        kwargs.pop('bg', None)

    click.secho(text, **kwargs)


def get_incremented_file_path(file_path):
    """
    Convert filename to incremented if exist

    For example:
    Convert foo/snippet.txt to foo/snippet-1.txt if foo/snippet.txt already exist.
    """
    if not os.path.exists(file_path):
        return file_path

    dir_path, basename = os.path.split(file_path)
    filename, ext = os.path.splitext(basename)

    i = 1
    incremented_filename = "{}-{}{}".format(filename, i, ext)
    new_path = os.path.join(dir_path, incremented_filename)
    while os.path.exists(new_path):
        incremented_filename = "{}-{}{}".format(filename, i, ext)
        new_path = os.path.join(dir_path, incremented_filename)
        i += 1

    return new_path


def read_metadata(config, owner=None):
    """Read meta file content"""
    if not owner:
        owner = config.get('snipper', 'username')

    with open(os.path.join(config.get('snipper', 'snippet_dir'), '{}.json'.format(owner)), 'r') as file:
        return json.loads(file.read())


def update_metadata(config, data, owner=None):
    """Update local metadata file that keeps all snippet's data"""
    if not owner:
        owner = config.get('snipper', 'username')

    with open(os.path.join(config.get('snipper', 'snippet_dir'), '{}.json'.format(owner)), 'w') as file:
        file.write(json.dumps(data))
