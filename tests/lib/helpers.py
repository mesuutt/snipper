import os
from os import path as osp
import tempfile
from functools import wraps

ospd = osp.dirname

GIT_REPO = os.environ.get("GIT_PYTHON_TEST_GIT_REPO_BASE", ospd(ospd(ospd(__file__))))


def with_rw_repo(working_tree_ref, bare=False):

    def argument_passer(func):
        @wraps(func)
        def repo_creator(self):
            prefix = 'non_'
            if bare:
                prefix = ''
            # END handle prefix
            repo_dir = tempfile.mktemp(prefix="%sbare_%s" % (prefix, func.__name__))
            rw_repo = self.rorepo.clone(repo_dir, shared=True, bare=bare, n=True)

            rw_repo.head.commit = rw_repo.commit(working_tree_ref)
            if not bare:
                rw_repo.head.reference.checkout()
            # END handle checkout

            prev_cwd = os.getcwd()
            os.chdir(rw_repo.working_dir)
            try:
                try:
                    return func(self, rw_repo)
                except:
                    log.info("Keeping repo after failure: %s", repo_dir)
                    repo_dir = None
                    raise
            finally:
                os.chdir(prev_cwd)
                rw_repo.git.clear_cache()
                rw_repo = None
                import gc
                gc.collect()
                if repo_dir is not None:
                    rmtree(repo_dir)
                # END rm test repo if possible
            # END cleanup
        # END rw repo creator
        return repo_creator
    # END argument passer
    return argument_passer
