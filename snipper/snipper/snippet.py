import os
import glob
import json
import re
import subprocess

import click

import utils

class Snippet(object):

    def __init__(self, config, username, snippet_id):
        self.config = config
        self.username = username
        self.snippet_id = snippet_id

        self.repo_path = self.get_path()

    def get_path(self):
        repo_parent = os.path.join(self.config.get('snippet_home'), self.username)
        matched_path = glob.glob(os.path.join(repo_parent, '*{}'.format(self.snippet_id)))

        return matched_path[0] if matched_path else None


    @staticmethod
    def clone(url, clone_to):
        """Clone repo"""

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
        """Pull changes from remote repo"""

        click.secho('Pulling local snippet: {}'.format(repo_dir), fg='blue')

        if os.path.exists(os.path.join(repo_dir, '.hg')):
            subprocess.call(['hg', 'pull', '--cwd={}'.format(repo_dir)], stderr=subprocess.STDOUT)
        else:
            subprocess.call(['git', '--git-dir={}/.git'.format(repo_dir), 'pull'])

    def get_files(self):
        """ Get files in local snippet directory """
        metadata_file = os.path.join(self.config.get('snippet_home'), 'metadata.json')
        with open(metadata_file, 'r') as file:
            data = json.loads(file.read())

            for item in data['values']:
                if item['id'] != self.snippet_id:
                    continue

                return [f for f in os.listdir(self.repo_path) if os.path.isfile(os.path.join(self.repo_path, f))]

    @staticmethod
    def clone_by_snippet_id(config, snippet_id):
        """
        Clone snippet from remote to local by snippet id
        Using for cloning new created snippet.
        """

        with open(config.get('metadata_file'), 'r') as file:
            metadata_file_content = json.loads(file.read())

        # Get snippet metadata from metadata file for cloning
        for item in metadata_file_content['values']:
            if item['id'] == snippet_id:
                metadata = item
                break

        owner_username = metadata['owner']['username']
        repo_parent = os.path.join(config.get('snippet_home'), owner_username)

        # Find snippet dirs which ends with specified snippet_id for checking
        # snippet cloned before

        # Clone repo over ssh (1)
        clone_url = metadata['links']['clone'][1]['href']
        clone_to = os.path.join(repo_parent, snippet_id)

        if metadata['title']:

            slugified_title = utils.slugify(metadata['title'])
            # Create dir name for snippet for clonning
            # Using title for readablity(<slugified snippet_title>-<snippet_id>)
            clone_to = os.path.join(repo_parent, "{}-{}".format(slugified_title, snippet_id))

        click.secho('Created snippet clonning...', fg='blue')
        Snippet.clone(clone_url, clone_to=clone_to)

    @staticmethod
    def add_snippet_metadata(config, snippet_metadata):
        """Open file reading and writing"""

        with open(config.get('metadata_file'), 'r+') as file:
            metadata = json.loads(file.read())
            file.seek(0)
            metadata['values'].append(snippet_metadata)

            file.write(json.dumps(metadata))


