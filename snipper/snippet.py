import os
from os import path
import glob
import json
import subprocess


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
        subprocess.call(['git', 'clone', url, clone_to])

    @staticmethod
    def pull(repo_dir):
        # TODO: Add log line for notifying user.
        subprocess.call(['git', '--git-dir={}/.git'.format(repo_dir), 'pull'])

    def get_files(self):
        metadata_file = path.join(self.config.get('snippet_home'), 'metadata.json')
        with open(metadata_file, 'r') as f:
            data = json.loads(f.read())

            for item in data['values']:
                if item['id'] != self.snippet_id:
                    continue

                return [f for f in os.listdir(self.repo_path) if path.isfile(path.join(self.repo_path, f))]
