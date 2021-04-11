import os
import re
import json
import unittest
import configparser
import tempfile
from copy import deepcopy
import shutil

from snipper.snippet import Snippet
from snipper.completers import SnippetDirCompleter, SnippetFileCompleter

TEST_DIR = os.path.dirname(__file__)

config = configparser.ConfigParser()
config.read(os.path.join(TEST_DIR, 'snipperrc'))

snippet_parent_dir = tempfile.mktemp(prefix='snipper_home_')
os.mkdir(snippet_parent_dir)
config.set('snipper', 'snippet_dir', snippet_parent_dir)

user_metadata_file = os.path.join(snippet_parent_dir, 'mesuutt.json')
shutil.copyfile(os.path.join(TEST_DIR, 'example_metadata.json'), user_metadata_file)

with open(os.path.join(TEST_DIR, 'example_git_snippet_data.json'), 'r') as snippet_file:
    git_snippet_data = json.loads(snippet_file.read())

snippet1 = Snippet(config, deepcopy(git_snippet_data))
event = snippet1.clone()
event.wait()


class PromptToolkitCompleterTestCase(unittest.TestCase):

    def test_fuzzy_snippet_dir_finder(self):
        """Test snippet directory fuzzy finder completer"""
        completer = SnippetDirCompleter(config)
        matched_dirs = completer.fuzzyfinder('testgit', completer.collection)
        self.assertEqual(matched_dirs, ['test-snippet-git--kBkKj'])

    def test_fuzzy_snippet_file_finder(self):
        """Test snippet file fuzzy finder completer"""
        completer = SnippetFileCompleter(config)
        matched_files = completer.fuzzyfinder('gitfile', completer.collection)
        should_match = ['test-snippet-git--kBkKj/file.txt']

        self.assertEqual(matched_files, should_match)
