import os
import requests

BITBUCKET_API_URL = 'https://api.bitbucket.org/2.0'


class BitbucketApi(object):
    base_url = BITBUCKET_API_URL

    def __init__(self, config):
        self.config = config

    def get(self, endpoint):
        username = self.config.get('snipper', 'username')
        password = self.config.get('snipper', 'password')

        res = requests.get(self.build_endpoint(endpoint), auth=(username, password))
        res.raise_for_status()

        return res

    def build_endpoint(self, endpoint):
        return os.path.join(self.base_url, endpoint)


class SnippetApi(BitbucketApi):
    base_url = '{}/snippets'.format(BITBUCKET_API_URL)

    def get_all(self):
        res = self.get(self.config.get('snipper', 'username'))
        return res.json()

    def make_payload(self, is_private, title, scm):
        payload = {}

        if is_private is not None:
            payload.update({'is_private': is_private})
        if title is not None:
            payload.update({'title': title})
        if scm is not None:
            payload.update({'scm': scm})

        return payload

    def create_snippet(self, file_list, is_private, title, scm):

        username = self.config.get('snipper', 'username')
        password = self.config.get('snipper', 'password')

        payload = self.make_payload(is_private, title, scm)

        response = requests.post(
            self.base_url,
            data=payload,
            files=file_list,
            auth=(username, password),
        )

        return response
