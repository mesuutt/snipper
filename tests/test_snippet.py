import os
import re
import json
import unittest
import configparser
import tempfile
from copy import deepcopy

from snipper.snippet import Snippet
from snipper import utils
# from snipper.tests import config, TEST_DIR

TEST_DIR = os.path.dirname(__file__)

config = configparser.ConfigParser()
config.read(os.path.join(TEST_DIR, 'snipperrc'))

snippet_parent_dir = tempfile.mktemp(prefix='snipper_test_repo_')
os.mkdir(snippet_parent_dir)

config.set('snipper', 'snippet_dir', snippet_parent_dir)

with open(os.path.join(TEST_DIR, 'example_git_snippet_data.json'), 'r') as snippet_file:
    git_snippet_data = json.loads(snippet_file.read())


class SnippetTestMixin:

    def test_commiting_snippet(self):
        with open(os.path.join(self.snippet.get_path(), 'foo.txt'), 'w+') as file:
            file.write('test content')

        event = self.snippet.commit(message='foo.txt added')
        event.wait()

        self.assertEqual(event.stderr.read(), '')

    def test_pulling_snippet(self):
        event = self.snippet.pull()

        self.assertEqual(event.stderr.read(), '')

    def test_pushing_snippet_to_remote(self):
        """We dont have to access rights to repo.

        So we should get access denied error
        """
        self.snippet.push()

    def test_getting_snippet_path(self):
        """Test snippet path is matching with regex pattern"""
        path = self.snippet.get_path()
        re.match(r'^%s\/[\w-]+\w{5}$' % self.snippet_parent_dir, path).group()

    def test_slugified_snippet_directory_name(self):
        slufified_title = utils.slugify(self.data['title'])
        dir_name = "{}-{}".format(slufified_title, self.data['id'])

        self.assertEqual(self.snippet.get_slugified_dirname(), dir_name)

    def test_getting_files_of_snippet(self):

        # Add new file before check file exist
        with open(os.path.join(self.snippet.get_path(), 'bar.txt'), 'w+') as file:
            file.write('test content')

        file_names = self.snippet.get_files()

        self.assertTrue('bar.txt' in file_names)

    def test_snippet_is_exists(self):
        self.assertTrue(self.snippet.is_exists())

    def test_updating_snippet_directory_name(self):
        """Change snippet title and check snippet dir name updated"""
        self.snippet.data['title'] = 'foo bar baz'
        self.snippet.update_dir_name()

        dir_name = "{}-{}".format('foo-bar-baz', self.data['id'])
        self.assertEqual(self.snippet.get_slugified_dirname(), dir_name)

    def test_clone_url_is_matching(self):
        """Test getting clone url is working"""
        clone_url = self.snippet.get_clone_url()

        # Get ssh clone url
        url = self.snippet.data['links']['clone'][1]['href']

        self.assertEqual(clone_url, url)

    def test_getting_details_of_snippet(self):
        text = self.snippet.get_detail_for_print()

        self.assertTrue(text.startswith('Title'))


class GitSnippetTestCase(SnippetTestMixin, unittest.TestCase):

    def setUp(self):
        self.snippet_parent_dir = snippet_parent_dir
        self.data = deepcopy(git_snippet_data)
        self.snippet = Snippet(config, self.data)

    def test_clone_snippet(self):
        """Test cloning snippet

        test method name contains _aaa_ for execute before another tests
        because some tests dependent to repo exist in file system.
        """
        event = self.snippet.clone()
        event.wait()

        self.assertTrue(event.stderr.read().startswith('Cloning into'))
