import os
import re
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

