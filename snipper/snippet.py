import os
import glob

from . import utils
from .repo import Repo


class Snippet(object):

    def __init__(self, config, data):
        self.config = config
        self.data = data

        self.snippet_id = data['id']

        self.repo_path = self.get_path()

        if os.path.exists(os.path.join(self.repo_path, '.hg')):
            self.scm = 'hg'
        else:
            self.scm = 'git'

    def is_exists(self):
        return os.path.exists(self.get_path())

    def get_path(self):
        repo_parent = self.config.get('snipper', 'snippet_dir')

        # Find snippet dirs which ends with specified snippet_id for checking
        matched_path = glob.glob(os.path.join(repo_parent, '*{}'.format(self.snippet_id)))
        if matched_path:
            return matched_path[0]

        # If snippet dir not found return generated path
        dir_name = self.get_slugified_dirname()
        new_path = os.path.join(repo_parent, dir_name)

        return new_path

    def get_slugified_dirname(self):
        slugified_title = utils.slugify(self.data['title'])
        return "{}-{}".format(slugified_title, self.data['id'])

    def update_dir_name(self):
        """Rename snippet directory with new title"""
        dir_name = self.get_slugified_dirname()
        new_path = os.path.join(self.config.get('snipper', 'snippet_dir'), dir_name)
        os.rename(self.repo_path, new_path)

    def pull(self):
        """Pull changes from remote repo"""
        return Repo.pull(self.repo_path)

    def commit(self, message='Snippet updated'):
        """Commit changes"""
        return Repo.commit(self.repo_path, message)

    def push(self):
        """Push changes to remote"""
        return Repo.push(self.repo_path)

    def sync(self):
        """Pull changes from remote and push changes to remote"""
        return Repo.sync(self.repo_path)

    def get_files(self):
        """Get files in local snippet directory"""
        return [f for f in os.listdir(self.repo_path) if os.path.isfile(os.path.join(self.repo_path, f))]

    def clone(self):
        repo_parent = os.path.dirname(self.repo_path)
        clone_to = os.path.join(repo_parent, self.data['id'])

        if self.data['title']:
            # Using title for readablity(<slugified snippet_title>-<snippet_id>)
            clone_to = os.path.join(repo_parent, self.get_slugified_dirname())

        return Repo.clone(self.get_clone_url(), clone_to=clone_to)

    def get_clone_url(self):
        # For py2 support converting to iterator

        return next(iter(filter(
            lambda x: x['name'] == self.config.get('snipper', 'protocol'),
            self.data['links']['clone']
        )))['href']

    def get_detail_for_print(self):

        text = "\n".join([
            u'Title     : {}'.format(self.data['title']),
            u'Is private: {}'.format("Yes" if self.data['is_private'] else "No"),
            u'Url       : {}'.format(self.data['links']['html']['href']),
            u'Owner     : {}'.format(self.data['owner']['username']),
            u'Path      : {}'.format(self.get_path()),
        ])

        return text
