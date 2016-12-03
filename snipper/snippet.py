import os
from os import path
import glob
import json
import re
import subprocess

import click

class Snippet(object):

    def __init__(self, config, username, snippet_id):
        self.config = config
        self.username = username
        self.snippet_id = snippet_id

        repo_parent = path.join(self.config.get('snippet_home'), username)
        self.repo_path = glob.glob(path.join(repo_parent, '*{}'.format(self.snippet_id)))[0]

    @staticmethod
    def clone(url, clone_to):

        #TODO: Add log line for notifying user.
        # subprocess.DEVNULL
        click.secho('Downloading snippet from remote', fg='green')

        try:
            repo_type = re.search(r'^(?:ssh|https)://(git|hg)', url).group(1)
        except AttributeError:
            click.secho('You can use snipper only with git or mercurial repositories', fg='red')

        if repo_type == "hg":
            subprocess.call(['hg', 'clone', url, clone_to])
        else:
            subprocess.call(['git', 'clone', url, clone_to])

    @staticmethod
    def pull(repo_dir):
        # TODO: Add log line for notifying user.

        click.secho('Updating local snippet: {}'.format(repo_dir), fg='green')

        if os.path.exists(os.path.join(repo_dir, '.hg')):
            subprocess.call(['hg', 'pull', '--cwd={}'.format(repo_dir)], stderr=subprocess.STDOUT)
        else:
            subprocess.call(['git', '--git-dir={}/.git'.format(repo_dir), 'pull'])

    def get_files(self):
        """ Return files of snippet """
        metadata_file = path.join(self.config.get('snippet_home'), 'metadata.json')
        with open(metadata_file, 'r') as file:
            data = json.loads(file.read())

            for item in data['values']:
                if item['id'] != self.snippet_id:
                    continue

                return [f for f in os.listdir(self.repo_path) if path.isfile(path.join(self.repo_path, f))]
