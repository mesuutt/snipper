import os
import unittest
import configparser
import tempfile
import shutil

from click.testing import CliRunner

from snipper import snipper

TEST_DIR = os.path.dirname(__file__)

config = configparser.ConfigParser()
config.read(os.path.join(TEST_DIR, 'snipperrc'))

snippet_parent_dir = tempfile.mktemp(prefix='snipper_home_')
os.mkdir(snippet_parent_dir)
config.set('snipper', 'snippet_dir', snippet_parent_dir)

snipperrc_file = os.path.join(snippet_parent_dir, 'snipperrc')
config.write(open(snipperrc_file, 'w'))

user_metadata_file = os.path.join(snippet_parent_dir, 'mesuutt.json')
shutil.copyfile(os.path.join(TEST_DIR, 'example_metadata.json'), user_metadata_file)


class CommandLineArgumentsTestCase(unittest.TestCase):

    def test_listing_snippets(self):
        runner = CliRunner()
        result = runner.invoke(snipper.cli, ['--config', snipperrc_file, 'ls'])

        self.assertEqual(result.exit_code, 0)

    def set_default_username_password(self):
        if not config.has_option('snipper', 'username') and not os.environ.get('SNIPPER_USERNAME'):
            self.assertTrue(False, 'Missing username setting. Set SNIPPER_USERNAME env variable or add username in tests/snipperrc')

        if not config.has_option('snipper', 'password') and not os.environ.get('SNIPPER_PASSWORD'):
            self.assertTrue(False, 'Missing password setting. Set SNIPPER_PASSWORD env variable or add password in tests/snipperrc')

        config.set('snipper', 'password', os.environ.get('SNIPPER_PASSWORD'))

    def test_pulling_snippets(self):
        self.set_default_username_password()

        runner = CliRunner()
        result = runner.invoke(snipper.cli, ['--config', snipperrc_file, 'pull'])

        self.assertEqual(result.exit_code, 0)

    def test_creating_new_snippet(self):
        self.set_default_username_password()

        runner = CliRunner()
        result = runner.invoke(snipper.cli, ['--config', snipperrc_file, 'new', '-t', 'testSnippetTitle'], input='test snippet content')

        self.assertEqual(result.exit_code, 0)

        # Burda metadata filei da kontrol et. Ayrica olusturulan dosyayida kontrol et.
