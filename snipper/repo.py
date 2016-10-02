import os
import json
import subprocess


class Repo(object):

    def __init__(self, config):
        self.config = config

    @staticmethod
    def clone(url, clone_to):
        #TODO: Add log line for notifying user.
        # subprocess.DEVNULL
        subprocess.call(['git', 'clone', url, clone_to])

    @staticmethod
    def pull(repo_dir):
        # TODO: Add log line for notifying user.
        subprocess.call(['git', '--git-dir={}/.git'.format(repo_dir), 'pull'])
