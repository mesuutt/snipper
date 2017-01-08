import os
import io
import json
import unittest
import configparser
import tempfile
import shutil

from snipper import utils

TEST_DIR = os.path.dirname(__file__)

config = configparser.ConfigParser()
config.read(os.path.join(TEST_DIR, 'snipperrc'))

snippet_parent_dir = tempfile.mktemp(prefix='snipper_home_')
os.mkdir(snippet_parent_dir)
config.set('snipper', 'snippet_dir', snippet_parent_dir)


class UtilsTestCase(unittest.TestCase):
    def test_open_files(self):
        temp_file = tempfile.mktemp()
        with open(temp_file, 'w') as file:
            file.write('snipper')

        # [('file', ('tmp0bui5f6p', <_io.BufferedReader name='/tmp/tmp0bui5f6p'>))]
        files = utils.open_files([temp_file])

        self.assertEqual(files[0][0], 'file')
        self.assertEqual(len(files[0][1]), 2)
        self.assertEqual(type(files[0][1][1]), io.BufferedReader)

    def test_slugify(self):
        self.assertEqual(utils.slugify(u'Test (File)'), 'test-file-')

    def test_secho(self):
        utils.secho(True, 'This text should be blue', fg='blue')
        utils.secho(False, 'This text should be uncolorized', fg='blue', bg='red')

    def test_get_incremented_file_path(self):
        temp_file = os.path.join(snippet_parent_dir, 'test_file.txt')
        with open(temp_file, 'w') as file:
            file.write('snipper')

        new_file_path = utils.get_incremented_file_path(temp_file)

        self.assertEqual(new_file_path, os.path.join(snippet_parent_dir, 'test_file-1.txt'))

    def test_reading_metadata(self):
        """Test reading metadata file"""
        # Copy example metadata file and test on copied file
        user_metadata_file = os.path.join(snippet_parent_dir, 'mesuutt.json')
        shutil.copy(os.path.join(TEST_DIR, 'example_metadata.json'), user_metadata_file)

        # Get without owner specified
        data = utils.read_metadata(config)
        self.assertIsNotNone(data)

        # Get with owner specified
        data = utils.read_metadata(config, owner='mesuutt')
        self.assertIsNotNone(data)

    def test_updating_metadata(self):
        """Test reading metadata file"""
        # Copy example metadata file and test on copied file
        user_metadata_file = os.path.join(snippet_parent_dir, 'mesuutt.json')
        shutil.copy(os.path.join(TEST_DIR, 'example_metadata.json'), user_metadata_file)

        with open(user_metadata_file, 'r') as file:
            data = json.loads(file.read())

        data['id'] = 'my_fake_id'

        # Test without owner
        utils.update_metadata(config, data)
        data = utils.read_metadata(config, owner='mesuutt')
        self.assertIsNotNone(data['id'], 'my_fake_id')

        # Test with owner
        utils.update_metadata(config, data, owner='mesuutt')
        data = utils.read_metadata(config, 'mesuutt')

        self.assertIsNotNone(data['id'], 'my_fake_id')

    def test_running_shell_command(self):
        utils.run_command("echo 'foo'")
