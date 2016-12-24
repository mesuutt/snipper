import os
import re
import shlex
from subprocess import Popen, DEVNULL, PIPE

import click


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
    process = Popen(shlex.split(cmd), stderr=PIPE, stdout=DEVNULL, universal_newlines=True)

    # If you want to sure process completed use p.wait()
    # If you will check process same as `process.stderr.read()` process will wait automatically.

    return process
