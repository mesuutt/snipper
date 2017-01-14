import os
import json
import unittest
import configparser

import httpretty

from snipper.api import SnippetApi
# from snipper.tests import config, TEST_DIR

TEST_DIR = os.path.dirname(__file__)

config = configparser.ConfigParser()
config.read(os.path.join(TEST_DIR, 'snipperrc'))


class BitbucketApiTestCase(unittest.TestCase):

    def setUp(self):
        self.api = SnippetApi(config)
        self.username = config.get('snipper', 'username')

    def test_build_endpoint(self):
        url = self.api.build_endpoint(self.username)
        return self.assertEqual(url, os.path.join(SnippetApi.base_url, self.username))

    @httpretty.activate
    def test_get_snippet_metadata(self):
        url = self.api.build_endpoint(self.username)

        with open(os.path.join(TEST_DIR, 'example_metadata.json'), 'r') as file:
            example_metadata_content = file.read()

        httpretty.register_uri(
            httpretty.GET,
            url,
            body=example_metadata_content,
            status=200,
            content_type='application/json',
        )

        metadata = self.api.get_all()

        self.assertEqual(metadata, json.loads(example_metadata_content))

    def test_make_payload(self):
        payload = self.api.make_payload(True, 'mytitle', 'git')

        self.assertEqual(payload, {'is_private': True, 'scm': 'git', 'title': 'mytitle'})

    @httpretty.activate
    def test_create_snippet(self):
        file_list = [('file', ('file.txt', 'content',),)]
        payload = {'title': 'title', 'scm': 'git', 'is_private': True}

        httpretty.register_uri(
            httpretty.POST,
            self.api.base_url,
            data=payload,
            files=file_list,
            status=201
        )

        response = self.api.create_snippet(file_list, True, 'mytitle', 'git')

        self.assertEqual(response.status_code, 201)
