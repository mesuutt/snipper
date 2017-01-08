import os
import re

from .utils import run_command


class Repo:

    @staticmethod
    def clone(url, clone_to):
        """Clone repo"""
        repo_type = re.search(r'^(?:ssh)://(git|hg)', url).group(1)

        if repo_type == "hg":
            cmd = 'hg clone {} {}'.format(url, clone_to)
        else:
            cmd = 'git clone {} {}'.format(url, clone_to)

        return run_command(cmd)

    @staticmethod
    def pull(repo_dir):
        """Pull changes from remote repo"""
        os.chdir(repo_dir)

        if os.path.exists(os.path.join(repo_dir, '.hg')):
            return run_command('hg pull; hg update')
        else:
            return run_command('git pull')

    @staticmethod
    def push(repo_dir):
        """Push changes to remote"""
        os.chdir(repo_dir)

        if os.path.exists(os.path.join(repo_dir, '.hg')):
            return run_command('hg push')
        else:
            return run_command('git push')

    @staticmethod
    def commit(repo_dir, message):
        """Commit changes"""
        os.chdir(repo_dir)

        if os.path.exists(os.path.join(repo_dir, '.hg')):
            run_command('hg add .')
            return run_command('hg commit -m {!r}'.format(message))
        else:
            run_command('git add -A')
            return run_command('git commit -m {!r}'.format(message))
